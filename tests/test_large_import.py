"""Large multipart dataset ingest: real chunked upload, HAM metadata and safe indexing.

Uses only synthetic tiny images for CI. It does not test clinical performance,
nor transfer an actual 1.3 GiB archive over GitHub Actions.
"""
import csv
import io
import zipfile

from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.api import app
from backend.db import Session, Dataset, Sample


def png(r, g, b):
    stream = io.BytesIO()
    Image.new('RGB', (24, 24), (r, g, b)).save(stream, format='PNG')
    return stream.getvalue()


def image_archive(records, unsafe=False):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        for key, color in records:
            archive.writestr('images/' + key + '.png', png(*color))
        if unsafe:
            archive.writestr('../unsafe.jpg', b'not-an-image')
    return stream.getvalue()


def ham_metadata(entries):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=['lesion_id', 'image_id', 'dx', 'dx_type', 'age', 'sex', 'localization'])
    writer.writeheader()
    for key, lesion, label in entries:
        writer.writerow({'lesion_id': lesion, 'image_id': key, 'dx': label,
                         'dx_type': 'consensus', 'age': '50', 'sex': 'unknown', 'localization': 'arm'})
    return buffer.getvalue().encode()


def initialize(client, name, blobs):
    payload = {'name': name, 'source': 'Generated synthetic image tests',
               'license': 'Synthetic test assets', 'modality': 'Research PNG',
               'files': [{'name': filename, 'size': len(data)} for filename, data in blobs]}
    response = client.post('/api/datasets/import-large', json=payload)
    assert response.status_code == 200, response.text
    assert response.json()['chunk_bytes'] == 8 * 1024 * 1024
    return response.json()['id']


def put_all(client, sid, blobs):
    for index, (_, data) in enumerate(blobs):
        # Split each tiny file into several chunks and verify confirmed byte offsets.
        offset = 0
        while offset < len(data):
            piece = data[offset:offset + 37]
            response = client.put(f'/api/datasets/import-large/{sid}/files/{index}?offset={offset}',
                                  content=piece, headers={'Content-Type': 'application/octet-stream'})
            assert response.status_code == 200, response.text
            offset += len(piece)
            assert response.json()['files'][index]['received'] == offset


def test_large_ham_import_matches_all_images_and_preserves_lesion_groups(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER', '1')
    images = [('ISIC_001', (20, 21, 22)), ('ISIC_002', (23, 24, 25)),
              ('ISIC_003', (26, 27, 28)), ('ISIC_004', (30, 31, 32)),
              ('ISIC_005', (33, 34, 35)), ('ISIC_006', (36, 37, 38))]
    archive_1 = image_archive(images[:3])
    archive_2 = image_archive(images[3:])
    metadata = ham_metadata([(images[0][0], 'lesion_1', 'nv'),
                             (images[1][0], 'lesion_1', 'nv'),
                             (images[2][0], 'lesion_2', 'mel'),
                             (images[3][0], 'lesion_3', 'bcc'),
                             (images[4][0], 'lesion_4', 'nv'),
                             (images[5][0], 'lesion_4', 'nv')])
    blobs = [('HAM10000_images_part_1.zip', archive_1),
             ('HAM10000_images_part_2.zip', archive_2),
             ('HAM10000_metadata.csv', metadata)]
    with TestClient(app) as client:
        sid = initialize(client, 'HAM Synthetic Test', blobs)
        put_all(client, sid, blobs)
        queued = client.post(f'/api/datasets/import-large/{sid}/process')
        assert queued.status_code == 200, queued.text
        status = client.get(f'/api/datasets/import-large/{sid}').json()
        assert status['phase'] == 'completed', status
        assert status['dataset_id']
        assert status['processed'] == 6
        assert status['total_images'] == 6
        did = status['dataset_id']
        detail = client.get(f'/api/datasets/{did}').json()
        assert detail['dataset']['sample_count'] == 6
        assert detail['dataset']['metadata']['import_format'] == 'ham10000_metadata'
        assert 'not_patient_independent' in detail['dataset']['metadata']['split_policy']
        with Session() as db:
            rows = db.scalars(select(Sample).where(Sample.dataset_id == did)).all()
            assert len(rows) == 6
            assert set(x.label for x in rows) == {'nv', 'mel', 'bcc'}
            assert all(x.sha256 and x.width == 24 and x.height == 24 for x in rows)
            by_lesion = {}
            for row in rows:
                assert row.group_type == 'lesion'
                by_lesion.setdefault(row.group_id, set()).add(row.split)
            assert all(len(splits) == 1 for splits in by_lesion.values())
        assert client.get('/api/privacy').status_code == 200


def test_missing_ham_part_fails_without_publishing_partial_dataset(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER', '1')
    before = None
    with TestClient(app) as client:
        before = client.get('/api/overview').json()['datasets']
        blobs = [('HAM10000_images_part_1.zip', image_archive([('ISIC_one', (1, 2, 3))])),
                 ('HAM10000_metadata.csv', ham_metadata([('ISIC_one', 'lesion_x', 'nv'),
                                                         ('ISIC_missing', 'lesion_y', 'mel')]))]
        sid = initialize(client, 'Incomplete HAM Synthetic', blobs)
        put_all(client, sid, blobs)
        response = client.post(f'/api/datasets/import-large/{sid}/process')
        assert response.status_code == 200, response.text
        status = client.get(f'/api/datasets/import-large/{sid}').json()
        assert status['phase'] == 'failed'
        assert 'missing or ambiguous' in status['error']
        assert client.get('/api/overview').json()['datasets'] == before


def test_large_import_rejects_bad_offsets_and_unsafe_zip_members(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER', '1')
    blob = image_archive([('ISIC_test', (50, 51, 52))], unsafe=True)
    csv_data = ham_metadata([('ISIC_test', 'lesion_abc', 'nv')])
    with TestClient(app) as client:
        blobs = [('HAM10000_images_part_1.zip', blob), ('HAM10000_metadata.csv', csv_data)]
        sid = initialize(client, 'Unsafe ZIP Synthetic', blobs)
        wrong_offset = client.put(f'/api/datasets/import-large/{sid}/files/0?offset=999',
                                  content=b'test')
        assert wrong_offset.status_code == 409
        assert 'expected 0' in wrong_offset.text
        put_all(client, sid, blobs)
        response = client.post(f'/api/datasets/import-large/{sid}/process')
        assert response.status_code == 200
        status = client.get(f'/api/datasets/import-large/{sid}').json()
        assert status['phase'] == 'failed'
        assert 'unsafe' in status['error'].lower()


def test_large_import_explicit_disk_cap_and_no_free_form_paths():
    with TestClient(app) as client:
        wrong = client.post('/api/datasets/import-large', json={
            'name': 'Bad file', 'files': [{'name': '../private.zip', 'size': 1234}]})
        assert wrong.status_code == 422
        cap = client.post('/api/datasets/import-large', json={
            'name': 'Oversized file', 'files': [{'name': 'images.zip', 'size': 9 * 1024 ** 3}]})
        assert cap.status_code == 422
        npz = client.post('/api/datasets/import-large', json={
            'name': 'Oversized NPZ', 'files': [{'name': 'big.npz', 'size': 600 * 1024 ** 2}]})
        assert npz.status_code == 422
