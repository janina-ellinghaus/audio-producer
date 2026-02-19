import os
import re
import shutil
import subprocess
import tempfile
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
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

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")[-4000:]
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

if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.post("/api/convert")
async def convert_audio(
    audio: UploadFile = File(...),
    cover: UploadFile = File(...),
    title: str = Form(...),
    album: str = Form(...),
    artist: str = Form(default="Unknown Artist"),
    year: Optional[str] = Form(default=None),
    track: Optional[str] = Form(default=None),
    genre: Optional[str] = Form(default=None),
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file required")
    if not cover.filename:
        raise HTTPException(status_code=400, detail="Cover art required")

    tmpdir = tempfile.mkdtemp()
    try:
        audio_in = os.path.join(tmpdir, "input")
        cover_in = os.path.join(tmpdir, "cover")
        mp3_out = os.path.join(tmpdir, "output.mp3")

        with open(audio_in, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        with open(cover_in, "wb") as f:
            shutil.copyfileobj(cover.file, f)

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

        cover_mime = _guess_cover_mime(cover.filename)
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
        return FileResponse(
            mp3_out,
            media_type="audio/mpeg",
            filename=safe_name,
            headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
        )
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
