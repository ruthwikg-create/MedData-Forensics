"""Disk-backed, bounded multi-archive imports for a single local research workstation.

Chunk upload never buffers an entire dataset in memory. The import's persistent
status permits polling and retry after a failed indexing attempt. This module
does not turn the research workbench into a public multi-user upload service.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import threading
import uuid
import zipfile
from contextlib import ExitStack
from pathlib import Path, PurePosixPath

from .db import DATA_ROOT, Session, Sample, jd
from .ingest import _dataset, import_npz
from .security import ALLOWED_EXT, MAX_IMAGE_BYTES, image_info, manifest_hash, sha_file

CHUNK_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 12 * 1024 ** 3
MAX_FILE_BYTES = 8 * 1024 ** 3
MAX_EXPANDED_BYTES = 20 * 1024 ** 3
MAX_IMAGE_COUNT = 100_000
MAX_CSV_BYTES = 32 * 1024 * 1024
UPLOAD_ROOT = DATA_ROOT / '.pending-imports'
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
_MUTEX = threading.RLock()
_SESSION_RE = re.compile(r'^[0-9a-f]{32}$')


def _directory(session_id):
    if not _SESSION_RE.fullmatch(str(session_id)):
        raise ValueError('Invalid upload session ID')
    return UPLOAD_ROOT / session_id


def _state(session_id):
    location = _directory(session_id) / 'state.json'
    if not location.is_file():
        raise ValueError('Upload session not found')
    return json.loads(location.read_text(encoding='utf-8'))


def _save(state):
    location = _directory(state['id'])
    location.mkdir(parents=True, exist_ok=True)
    staged = location / 'state.tmp'
    staged.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    os.replace(staged, location / 'state.json')


def _available_disk(bytes_needed):
    available = shutil.disk_usage(DATA_ROOT).free
    if available < bytes_needed + 512 * 1024 ** 2:
        raise ValueError('Insufficient free disk space for this import. Keep at least 512 MiB free beyond the incoming dataset.')


def create_session(name, source, license_name, modality, files, max_per_split=500):
    if not (2 <= len(name.strip()) <= 200):
        raise ValueError('Dataset name must contain 2–200 characters')
    if not (1 <= len(files) <= 6):
        raise ValueError('Select between one and six files (image ZIP parts and metadata CSV, or one NPZ)')
    records = []
    for record in files:
        filename = str(record.get('name', ''))
        size = record.get('size')
        if filename != Path(filename).name or '/' in filename or '\\' in filename or not filename.strip():
            raise ValueError('Files must have ordinary file names without folder paths')
        suffix = Path(filename).suffix.lower()
        if suffix not in ('.zip', '.csv', '.npz'):
            raise ValueError('Supported large-import files are .zip, .csv, and .npz')
        if type(size) is not int or not (0 < size <= MAX_FILE_BYTES):
            raise ValueError('Individual files must be nonempty and at most 8 GiB')
        records.append({'name': filename[:200], 'size': size, 'received': 0})
    if len({r['name'].casefold() for r in records}) != len(records):
        raise ValueError('Duplicate file names are not supported')
    total = sum(x['size'] for x in records)
    if total > MAX_TOTAL_BYTES:
        raise ValueError('The combined import exceeds the 12 GiB workstation safety limit')
    if any(r['name'].lower().endswith('.npz') for r in records) and (len(records) != 1 or total > 256 * 1024 ** 2):
        raise ValueError('MedMNIST NPZ import currently supports one archive up to 256 MiB. Large multi-file imports support ZIP and CSV.')
    if not any(r['name'].lower().endswith(('.npz', '.zip')) for r in records):
        raise ValueError('Select at least one ZIP image archive or MedMNIST NPZ')
    if not (10 <= max_per_split <= 10_000):
        raise ValueError('Maximum NPZ images per split must be 10–10,000')
    _available_disk(total)
    session_id = uuid.uuid4().hex
    state = {'id': session_id, 'phase': 'uploading', 'name': name.strip(),
             'source': source[:255], 'license': license_name[:250], 'modality': modality[:120],
             'max_per_split': max_per_split, 'files': records,
             'total_bytes': total, 'received_bytes': 0, 'processed': 0, 'total_images': 0,
             'message': 'Upload initialized; images remain on this computer.',
             'dataset_id': None, 'error': None}
    with _MUTEX:
        _save(state)
    return public_status(state)


def public_status(state):
    return {k: state[k] for k in
            ('id', 'phase', 'files', 'received_bytes', 'total_bytes', 'processed',
             'total_images', 'message', 'dataset_id', 'error')}


def status(session_id):
    with _MUTEX:
        state = _state(session_id)
        if state['phase'] == 'processing' and state.get('pid') != os.getpid():
            state.update(phase='failed', error='Local server restarted during indexing. You can retry without re-uploading.',
                         message='Indexing was interrupted; original uploaded archives are retained.')
            _save(state)
        return public_status(state)


def append_chunk(session_id, file_index, offset, content):
    if not isinstance(content, bytes) or not (0 < len(content) <= CHUNK_BYTES):
        raise ValueError('Each upload chunk must be between 1 byte and 8 MiB')
    with _MUTEX:
        state = _state(session_id)
        if state['phase'] != 'uploading':
            raise ValueError('This upload is no longer accepting chunks')
        if not (0 <= file_index < len(state['files'])):
            raise ValueError('Invalid upload file index')
        file = state['files'][file_index]
        if offset != file['received']:
            raise ValueError(f'Unexpected upload offset: expected {file["received"]} bytes')
        if offset + len(content) > file['size']:
            raise ValueError('Upload chunk exceeds declared file size')
        dest = _directory(session_id) / f'{file_index}.upload'
        with open(dest, 'ab') as stream:
            stream.write(content)
        file['received'] += len(content)
        state['received_bytes'] += len(content)
        _save(state)
        return public_status(state)


def begin_processing(session_id):
    with _MUTEX:
        state = _state(session_id)
        if state['phase'] not in ('uploading', 'failed'):
            raise ValueError('This import is already queued, running, or complete')
        if any(row['received'] != row['size'] for row in state['files']):
            raise ValueError('Finish uploading every selected ZIP and metadata CSV before indexing')
        state.update(phase='queued', error=None, message='Archives received; waiting for local indexing.')
        _save(state)
        return public_status(state)


def _update(session_id, **changes):
    with _MUTEX:
        state = _state(session_id)
        state.update(changes)
        _save(state)


def _zip_entry_safe(info):
    name = info.filename
    p = PurePosixPath(name)
    if (not name or name.startswith(('/', '\\')) or '\\' in name or
            any(part in ('.', '..') for part in p.parts) or
            (info.external_attr >> 16) & 0o170000 == 0o120000 or
            info.flag_bits & 0x1):
        raise ValueError('ZIP contains an unsafe, encrypted, or linked path')
    if info.file_size > MAX_EXPANDED_BYTES:
        raise ValueError('ZIP member exceeds expanded size limit')
    return not info.is_dir()


def _load_rows(csv_bytes):
    if not (0 < len(csv_bytes) <= MAX_CSV_BYTES):
        raise ValueError('Metadata CSV is empty or too large (32 MiB maximum)')
    try:
        text = csv_bytes.decode('utf-8-sig')
    except UnicodeDecodeError as ex:
        raise ValueError('Metadata CSV must be UTF-8 encoded') from ex
    reader = csv.DictReader(io.StringIO(text))
    cols = set(reader.fieldnames or [])
    ham = {'image_id', 'dx', 'lesion_id'}.issubset(cols)
    generic = {'sample_id', 'image_path', 'label', 'split'}.issubset(cols)
    if not ham and not generic:
        raise ValueError('Provide HAM10000_metadata.csv with image_id, dx, lesion_id; or samples.csv with sample_id, image_path, label, split')
    rows = []
    seen = set()
    for row in reader:
        if len(rows) >= MAX_IMAGE_COUNT:
            raise ValueError('Too many metadata rows (100,000 maximum)')
        key = (row.get('image_id') if ham else row.get('sample_id') or '').strip()
        if not key or key in seen:
            raise ValueError('Metadata contains blank or duplicate image identifiers')
        seen.add(key)
        if ham and (not row.get('dx') or not row.get('lesion_id')):
            raise ValueError('HAM10000 records require both diagnosis and lesion_id')
        if not ham and row.get('split') not in ('train', 'val', 'test'):
            raise ValueError('Explicit CSV splits must be train, val or test')
        rows.append(row)
    if not rows:
        raise ValueError('Metadata CSV contains no image records')
    return rows, ham


def _lesion_split(value):
    # Exploratory lesion-grouped split ONLY; it is not a verified patient split
    # and not the official ISIC challenge test partition.
    digest = hashlib.sha256(('mdf-ham10000-lesion-split-v1|' + value).encode()).digest()
    bucket = int.from_bytes(digest[:8], 'big') % 100
    return 'train' if bucket < 80 else ('val' if bucket < 90 else 'test')


def _index_zip_collection(session_id, state):
    with ExitStack() as stack:
        archives = []
        lookup = {}
        csv_candidates = []
        expanded = 0
        for i, record in enumerate(state['files']):
            suffix = Path(record['name']).suffix.lower()
            path = _directory(session_id) / f'{i}.upload'
            if suffix == '.csv':
                if path.stat().st_size > MAX_CSV_BYTES:
                    raise ValueError('Metadata CSV exceeds the 32 MiB limit')
                csv_candidates.append((record['name'], path.read_bytes()))
                continue
            if suffix != '.zip':
                raise ValueError('ZIP + CSV imports cannot include NPZ files')
            archive = stack.enter_context(zipfile.ZipFile(path))
            archives.append(archive)
            infos = archive.infolist()
            if len(infos) > 120_000:
                raise ValueError('ZIP archive contains too many entries')
            for item in infos:
                if not _zip_entry_safe(item):
                    continue
                expanded += item.file_size
                if expanded > MAX_EXPANDED_BYTES:
                    raise ValueError('Combined ZIP expanded size exceeds the 20 GiB safety cap')
                suffix2 = PurePosixPath(item.filename).suffix.lower()
                base = PurePosixPath(item.filename).name
                if suffix2 == '.csv' and base.lower() in ('samples.csv', 'ham10000_metadata.csv'):
                    if item.file_size > MAX_CSV_BYTES:
                        raise ValueError('Metadata CSV exceeds 32 MiB')
                    csv_candidates.append((item.filename, archive.read(item)))
                if suffix2 not in ALLOWED_EXT:
                    continue
                if item.file_size > MAX_IMAGE_BYTES:
                    raise ValueError('Individual image exceeds the 20 MiB safety cap')
                if base in lookup:
                    raise ValueError('Multiple image archives contain the same filename: ' + base)
                lookup[base] = (archive, item)
        if not archives:
            raise ValueError('At least one image ZIP archive is required')
        if len(csv_candidates) != 1:
            raise ValueError('Select one metadata CSV, plus the image ZIP archives. For HAM10000 choose HAM10000_metadata.csv and both image ZIP parts together.')
        rows, ham = _load_rows(csv_candidates[0][1])
        refs = []
        for row in rows:
            if ham:
                key = row['image_id'].strip()
                candidates = [key + ext for ext in ('.jpg', '.jpeg', '.png', '.webp')]
                matches = [lookup[x] for x in candidates if x in lookup]
            else:
                requested = row['image_path'].replace('\\', '/')
                if '..' in PurePosixPath(requested).parts or requested.startswith('/'):
                    raise ValueError('CSV contains an unsafe image path')
                matches = [lookup[PurePosixPath(requested).name]] if PurePosixPath(requested).name in lookup else []
            if len(matches) != 1:
                raise ValueError('Metadata image is missing or ambiguous in selected ZIP parts: ' +
                                 (row.get('image_id') or row.get('image_path') or '')[:100] +
                                 '. Include all image ZIP parts and matching metadata.')
            refs.append(matches[0])
        estimated = sum(info.file_size for _, info in refs)
        _available_disk(estimated)
        _update(session_id, total_images=len(rows),
                message=f'Indexing {len(rows)} images with bounded disk streaming. No estimated completion time.')
        with Session() as db:
            d = _dataset(state['name'], state['source'], state['license'], state['modality'],
                         'Disk-streamed ZIP/CSV research import; originals retained in the source archives only until import completes.',
                         False, {'import_format': 'ham10000_metadata' if ham else 'samples_csv',
                                 'split_policy': ('deterministic_lesion_group_80_10_10_exploratory_not_patient_independent'
                                                  if ham else 'provided_csv_splits'),
                                 'grouping_warning': ('HAM10000 lesion_id groups images of a lesion, not necessarily an independent patient.'
                                                      if ham else 'Group independence depends on supplied metadata.'),
                                 'source_files': [f['name'] for f in state['files']],
                                 'source_image_count': len(rows)})
            db.add(d)
            db.flush()
            dest = DATA_ROOT / d.id / 'images'
            dest.mkdir(parents=True, exist_ok=True)
            samples = []
            try:
                for index, (row, (archive, member)) in enumerate(zip(rows, refs)):
                    ext = PurePosixPath(member.filename).suffix.lower()
                    out = dest / f'{index:07d}{ext}'
                    count = 0
                    with archive.open(member) as source, out.open('wb') as target:
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            count += len(block)
                            if count > MAX_IMAGE_BYTES:
                                raise ValueError('Image exceeded the expanded per-image size cap')
                            target.write(block)
                    try:
                        width, height = image_info(out)
                    except ValueError:
                        width = height = None  # Retain as an invalid image for integrity audit.
                    lesion = (row.get('lesion_id') or '').strip() if ham else (
                        row.get('lesion_id') or row.get('group_id') or row.get('patient_id') or '').strip()
                    group_type = ('lesion' if ham or row.get('lesion_id') else
                                  'patient' if row.get('patient_id') else
                                  'unspecified' if lesion else None)
                    sample = Sample(
                        dataset_id=d.id,
                        sample_id=(row['image_id'] if ham else row['sample_id'])[:200],
                        relpath=f'{d.id}/images/{out.name}',
                        label=(row['dx'] if ham else row['label'])[:120],
                        split=(_lesion_split(lesion) if ham else row['split']),
                        group_id=lesion or None, group_type=group_type,
                        site=row.get('site_id') or None,
                        source_id=row.get('image_id') if ham else row.get('source_record_id'),
                        sha256=sha_file(out), width=width, height=height,
                        meta=jd(dict(row)))
                    samples.append(sample)
                    if index % 32 == 0 or index + 1 == len(rows):
                        _update(session_id, processed=index + 1, message=f'Indexed {index + 1} / {len(rows)} images')
                db.add_all(samples)
                d.manifest_hash = manifest_hash(samples)
                db.commit()
                return d.id
            except Exception:
                db.rollback()
                shutil.rmtree(DATA_ROOT / d.id, ignore_errors=True)
                raise


def process_session(session_id):
    try:
        with _MUTEX:
            state = _state(session_id)
            if state['phase'] != 'queued':
                return
            state.update(phase='processing', pid=os.getpid(),
                         message='Validating archives and metadata before extracting images.')
            _save(state)
        if len(state['files']) == 1 and state['files'][0]['name'].lower().endswith('.npz'):
            index_path = _directory(session_id) / '0.upload'
            dataset_id = import_npz(index_path, state['name'], state['source'],
                                    state['license'], state['max_per_split'])
        else:
            dataset_id = _index_zip_collection(session_id, state)
        _update(session_id, phase='completed', dataset_id=dataset_id,
                message='Research dataset imported and indexed. Review split policy and label provenance.',
                error=None)
        # Uploaded source archives no longer needed; indexed image records remain.
        for i in range(len(state['files'])):
            (_directory(session_id) / f'{i}.upload').unlink(missing_ok=True)
    except Exception as exc:
        _update(session_id, phase='failed', error=f'{type(exc).__name__}: {exc}'[:600],
                message='Import failed. Archives remain staged locally for a retry; review the error.')
