"""Strict local-path and upload checks. No cloud or external calls."""
from pathlib import Path
import hashlib, os, secrets
from PIL import Image, UnidentifiedImageError
from .db import DATA_ROOT

MAX_IMAGE_BYTES = 20*1024*1024
MAX_ARCHIVE_BYTES = 150*1024*1024  # ZIP packages: retain strict compressed-size cap
MAX_NPZ_BYTES = 256*1024*1024  # NPZ packages: includes standard PathMNIST archive
MAX_PIXELS = 25_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
ALLOWED_EXT={'.png','.jpg','.jpeg','.webp','.bmp','.tif','.tiff'}

def safe_path(relpath):
    if not relpath or not isinstance(relpath,str): raise ValueError('Invalid path')
    target=(DATA_ROOT/relpath).resolve()
    if not target.is_relative_to(DATA_ROOT): raise ValueError('Path escapes dataset storage')
    return target

def image_info(path):
    path=Path(path)
    if path.suffix.lower() not in ALLOWED_EXT: raise ValueError('Unsupported image type')
    if path.stat().st_size > MAX_IMAGE_BYTES: raise ValueError('Image exceeds size limit')
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
            if im.width*im.height>MAX_PIXELS: raise ValueError('Image exceeds pixel limit')
            return im.size
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as ex:
        raise ValueError(f'Unreadable or unsafe image: {ex}') from ex

def sha_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def manifest_hash(rows):
    h=hashlib.sha256()
    for x in sorted(rows,key=lambda r:r.sample_id):
        h.update(f'{x.sample_id}|{x.label}|{x.split}|{x.group_id}|{x.sha256}\n'.encode())
    return h.hexdigest()

def extract_auth(request):
    # Local workstation only; optional secret for LAN access. Bind 127.0.0.1 by default.
    token=os.getenv('MDF_ACCESS_TOKEN','')
    if token:
        candidate=request.headers.get('X-MDF-Token','') or request.cookies.get('mdf_access','')
        if not secrets.compare_digest(candidate,token): return False
    return True
