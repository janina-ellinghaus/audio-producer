import os
import re
import shutil
import subprocess
import tempfile
import logging
from typing import Optional
from datetime import datetime;
from dotenv import load_dotenv;

from fastapi import FastAPI, File, Form, UploadFile, HTTPException

from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import backend.mp3

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_PATH)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _safe_filename(value: str, default: str = "output") -> str:
    value = (value or "").strip()
    if not value:
        return default
    value = re.sub(r"[^\w\-. ]+", "_", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:120] or default




def _guess_cover_mime(filename: str) -> str:
    f = (filename or "").lower()
    if f.endswith(".png"):
        return "image/png"
    return "image/jpeg"




def _save_upload_file(upload: UploadFile, dst_path: str) -> None:
    with open(dst_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)


def _resolve_cover_path(tmpdir: str) -> str:
    cover_in = os.path.join(tmpdir, "cover")
    default_cover_path = "./media/default_cover.jpg"
    if os.path.exists(default_cover_path):
        shutil.copy2(default_cover_path, cover_in)
        logger.debug(f"Using default cover from {default_cover_path}")
        return cover_in

    raise HTTPException(status_code=500, detail="Default cover art not found")



def _build_mp3_response(mp3_out: str, title: str) -> StreamingResponse:
    safe_name = _safe_filename(title, "output") + ".mp3"

    # Read the MP3 file into memory so we can delete the temp directory
    with open(mp3_out, "rb") as f:
        mp3_data = f.read()

    logger.debug(f"Read MP3 data: {len(mp3_data)} bytes")
    return StreamingResponse(
        iter([mp3_data]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/convert")
async def convert_audio(
    audioFile: UploadFile = File(...),
    topic: str = Form(...),
    speaker: str = Form(default="Unknown Speaker"),
):
    title = f"{topic}{os.environ['TITLE_SUFFIX']}"

    if not audioFile.filename:
        raise HTTPException(status_code=400, detail="Audio file required")

    tmpdir = tempfile.mkdtemp()
    logger.debug(f"Created temp directory: {tmpdir}")
    try:
        audio_in = os.path.join(tmpdir, "input")
        mp3_out = os.path.join(tmpdir, "output.mp3")

        _save_upload_file(audioFile, audio_in)
        logger.debug(f"Saved audio to {audio_in}, size: {os.path.getsize(audio_in)} bytes")

        cover_in = _resolve_cover_path(tmpdir)

        backend.mp3.convert_to_mp3(audio_in, mp3_out, logger)

        cover_mime = _guess_cover_mime("default_cover.jpg")
        backend.mp3.write_id3_tags(
            mp3_out,
            title=title,
            album=os.environ['ALBUM'],
            artist=speaker,
            year=str(datetime.now().year),
            track=None,
            genre=os.environ['GENRE'],
            cover_path=cover_in,
            cover_mime=cover_mime,
        )
        return _build_mp3_response(mp3_out, title)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Conversion error: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
            logger.debug(f"Cleaned up temp directory: {tmpdir}")


if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
