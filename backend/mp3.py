import subprocess
import os.path
from typing import Optional

from fastapi import HTTPException
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC, TIT2, TALB, TPE1, TDRC, TRCK, TCON
from mutagen.mp3 import MP3

from backend import log
logger = log.getLogger(__name__)


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


def convert_to_mp3(audio_in: str, mp3_out: str) -> None:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            audio_in,
            "-vn",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            mp3_out,
        ],
    )

    logger.debug(f"FFmpeg completed, checking output file: {mp3_out}")
    if os.path.exists(mp3_out):
        logger.debug(f"Output file exists, size: {os.path.getsize(mp3_out)} bytes")
        return

    logger.error("Output file does not exist after FFmpeg conversion!")
    raise HTTPException(status_code=500, detail="FFmpeg conversion failed to produce output file")


def write_id3_tags(
    mp3_path: str,
    *,
    title: str,
    album: str,
    artist: str,
    year: Optional[str],
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

    if genre:
        tags.delall("TCON")
        tags.add(TCON(encoding=3, text=genre))

    tags.save(mp3_path, v2_version=3)
