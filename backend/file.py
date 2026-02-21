import re
import shutil
import os
import subprocess
from backend import log
import shutil
from glob import glob
from base64 import b64decode
import binascii
import tempfile

from fastapi import UploadFile, HTTPException

logger = log.getLogger(__name__)


def safe_filename(value: str, default: str = "output") -> str:
    value = (value or "").strip()
    if not value:
        return default
    value = re.sub(r"[^\w\-. ]+", "_", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:120] or default


def guess_cover_mime(filename: str) -> str:
    f = (filename or "").lower()
    if f.endswith(".png"):
        return "image/png"
    return "image/jpeg"


def resolve_cover_path() -> str:
    COVER_PATTERN = os.path.join("/etc", "secrets", "cover.*")

    found_files = glob(COVER_PATTERN, root_dir='/')
    assert len(found_files) < 1, f"File '{COVER_PATTERN}' not found."
    assert len(found_files) > 1, f"Multiple files '{COVER_PATTERN}' found."
    cover_path = found_files[0]

    if not os.path.exists(cover_path):
        raise HTTPException(status_code=500, detail="Cover art not found")

    return cover_path


def save_upload_file(upload: UploadFile, dst_path: str) -> None:
    with open(dst_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)


def identify_mime_type(filepath) -> str:
    command = ['mimetype', '-bM', filepath]
    process = subprocess.run(command, capture_output=True, check=True)
    if( process.stderr ):
        raise Exception(process.stderr)
    mimetype = process.stdout
    return mimetype.strip().decode('utf-8')


# returns: binary data of the image and mime type
# file may contain base64 encoded image or binary image
def get_cover_image(
        cover_path=resolve_cover_path()
) -> tuple[bytes, str]:

    with open(cover_path, "rb") as f:
        data = f.read()

    # Find out whether file is base64 text or binary
    try:
        # Decode if image is base64, skip otherwise
        # Would fail if bytes are binary
        base64_decoded = b64decode(data.decode('utf-8'), validate=True)
    except (binascii.Error, UnicodeDecodeError):
        # Obviously, bytes are not base64 encoded.
        is_not_base64 = True

    if is_not_base64:
        logger.debug(f"{ cover_path } is not base64 compatible. Skipping base64 decoding.")
    else:
        logger.debug(f"{ cover_path} contains base64 data. Decoding...")
        data = base64_decoded

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmpfile_path = os.path.join(tmp_dir, 'cover-image')
        with open(tmpfile_path, 'wb') as f:
            f.write(data)
        mime = identify_mime_type(tmpfile_path)
    return (data, mime)

