"""Strict local-path and upload checks. No cloud or external calls."""
from pathlib import Path
import hashlib, ipaddress, os, secrets, threading, time
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

# An opaque bearer credential is stored in the browser cookie, never the
# workstation-wide MDF_ACCESS_TOKEN. The session registry is deliberately
# process-local: restarting the single-user server revokes all browser sessions.
SESSION_SECONDS = 8 * 3600
_MAX_SESSIONS = 128
_sessions = {}
_session_lock = threading.Lock()


def loopback_host(host):
    host = str(host or '').strip().lower().strip('[]')
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _local_request(request):
    # Even if uvicorn was launched manually with --host 0.0.0.0, do not
    # silently authorize remote peers when there is no configured secret.
    if not loopback_host(os.getenv('MDF_HOST', '127.0.0.1')):
        return False
    peer = request.client.host if request.client else ''
    if peer == 'testclient':  # Starlette's in-process TestClient, never a TCP IP.
        return True
    try:
        return ipaddress.ip_address(peer.split('%', 1)[0]).is_loopback
    except ValueError:
        return False


def _valid_session(cookie):
    if not cookie:
        return False
    with _session_lock:
        expiry = _sessions.get(cookie)
        if expiry is None:
            return False
        if expiry <= time.monotonic():
            _sessions.pop(cookie, None)
            return False
        return True


def new_session():
    with _session_lock:
        current = time.monotonic()
        for key, expiry in list(_sessions.items()):
            if expiry <= current:
                _sessions.pop(key, None)
        # Bound memory if an authenticated client repeatedly creates sessions.
        while len(_sessions) >= _MAX_SESSIONS:
            _sessions.pop(next(iter(_sessions)))
        identifier = secrets.token_urlsafe(32)
        _sessions[identifier] = current + SESSION_SECONDS
        return identifier


def revoke_session(cookie):
    with _session_lock:
        _sessions.pop(cookie, None)


def valid_master_token(candidate):
    expected = os.getenv('MDF_ACCESS_TOKEN', '')
    return bool(expected and candidate and secrets.compare_digest(candidate, expected))


def extract_auth(request):
    token = os.getenv('MDF_ACCESS_TOKEN', '')
    if not token:
        return _local_request(request)
    return valid_master_token(request.headers.get('X-MDF-Token', '')) or _valid_session(request.cookies.get('mdf_access', ''))
