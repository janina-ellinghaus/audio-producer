import os
import re
import shutil
import subprocess
import tempfile
import logging
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from mutagen.id3 import ID3, APIC, TIT2, TALB, TPE1, TDRC, TRCK, TCON
from mutagen.mp3 import MP3


def _safe_filename(value: str, default: str = "output") -> str:
    value = (value or "").strip()
    if not value:
        return default
    value = re.sub(r"[^\w\-. ]+", "_", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:120] or default


def _run_ffmpeg(args: list[str], timeout_s: int = 60) -> None:
    logger.debug(f"Running FFmpeg: {' '.join(args)}")
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=504, detail="Transcode timed out") from e

    logger.debug(f"FFmpeg return code: {proc.returncode}")
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")[-4000:]
        logger.error(f"FFmpeg failed: {stderr}")
        raise HTTPException(status_code=400, detail=f"FFmpeg failed: {stderr}")


def _guess_cover_mime(filename: str) -> str:
    f = (filename or "").lower()
    if f.endswith(".png"):
        return "image/png"
    return "image/jpeg"


def _write_id3_tags(
    mp3_path: str,
    *,
    title: str,
    album: str,
    artist: str,
    year: Optional[str],
    track: Optional[str],
    genre: Optional[str],
    cover_path: str,
    cover_mime: str,
) -> None:
    MP3(mp3_path).save()

    try:
        tags = ID3(mp3_path)
    except Exception:
        tags = ID3()

    tags.delall("APIC")
    tags.add(
        APIC(
            encoding=3,
            mime=cover_mime,
            type=3,
            desc="Cover",
            data=open(cover_path, "rb").read(),
        )
    )

    tags.delall("TIT2")
    tags.add(TIT2(encoding=3, text=title))

    tags.delall("TALB")
    tags.add(TALB(encoding=3, text=album))

    tags.delall("TPE1")
    tags.add(TPE1(encoding=3, text=artist))

    if year:
        tags.delall("TDRC")
        tags.add(TDRC(encoding=3, text=year))

    if track:
        tags.delall("TRCK")
        tags.add(TRCK(encoding=3, text=track))

    if genre:
        tags.delall("TCON")
        tags.add(TCON(encoding=3, text=genre))

    tags.save(mp3_path, v2_version=3)


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
    audio: UploadFile = File(...),
    cover: Optional[UploadFile] = File(default=None),
    title: str = Form(...),
    album: str = Form(...),
    artist: str = Form(default="Unknown Artist"),
    year: Optional[str] = Form(default=None),
    track: Optional[str] = Form(default=None),
    genre: Optional[str] = Form(default=None),
):
    cover_filename = cover.filename if cover else "default"
    logger.info(f"Converting audio: title={title}, album={album}, audio={audio.filename}, cover={cover_filename}")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file required")

    tmpdir = tempfile.mkdtemp()
    logger.debug(f"Created temp directory: {tmpdir}")
    try:
        audio_in = os.path.join(tmpdir, "input")
        cover_in = os.path.join(tmpdir, "cover")
        mp3_out = os.path.join(tmpdir, "output.mp3")

        with open(audio_in, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        logger.debug(f"Saved audio to {audio_in}, size: {os.path.getsize(audio_in)} bytes")

        # Use default cover if none provided
        if cover and cover.filename:
            with open(cover_in, "wb") as f:
                shutil.copyfileobj(cover.file, f)
            logger.debug(f"Saved cover to {cover_in}, size: {os.path.getsize(cover_in)} bytes")
        else:
            default_cover_path = "./media/default_cover.jpg"
            if os.path.exists(default_cover_path):
                shutil.copy2(default_cover_path, cover_in)
                logger.debug(f"Using default cover from {default_cover_path}")
            else:
                raise HTTPException(status_code=500, detail="Default cover art not found")

        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i", audio_in,
                "-vn",
                "-c:a", "libmp3lame",
                "-q:a", "2",
                mp3_out,
            ]
        )

        logger.debug(f"FFmpeg completed, checking output file: {mp3_out}")
        if os.path.exists(mp3_out):
            logger.debug(f"Output file exists, size: {os.path.getsize(mp3_out)} bytes")
        else:
            logger.error(f"Output file does not exist after FFmpeg conversion!")
            raise HTTPException(status_code=500, detail="FFmpeg conversion failed to produce output file")

        cover_mime = _guess_cover_mime(cover.filename if cover else "default_cover.jpg")
        _write_id3_tags(
            mp3_out,
            title=title,
            album=album,
            artist=artist,
            year=year,
            track=track,
            genre=genre,
            cover_path=cover_in,
            cover_mime=cover_mime,
        )

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
