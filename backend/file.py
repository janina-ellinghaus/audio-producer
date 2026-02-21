import re
import shutil
import os
from backend import log
import shutil

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


def resolve_cover_path(tmpdir: str ) -> str:
    cover_in = os.path.join(tmpdir, "cover")
    default_cover_path = "./media/default_cover.jpg"
    if os.path.exists(default_cover_path):
        shutil.copy2(default_cover_path, cover_in)
        logger.debug(f"Using default cover from {default_cover_path}")
        return cover_in

    raise HTTPException(status_code=500, detail="Default cover art not found")


def save_upload_file(upload: UploadFile, dst_path: str) -> None:
    with open(dst_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
