import os
import shutil
import tempfile
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, File, Form, UploadFile, HTTPException

from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend import mp3, file, log

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

load_dotenv(ENV_PATH)
logger = log.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_mp3_response(mp3_out: str, title: str) -> StreamingResponse:
    safe_name = file.safe_filename(title, "output") + ".mp3"

    # Read the MP3 file into memory so we can delete the temp directory
    with open(mp3_out, "rb") as f:
        mp3_data = f.read()

    logger.debug(f"Read MP3 data: {len(mp3_data)} bytes")
    return StreamingResponse(
        iter([mp3_data]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )



@app.post("/api/convert")
async def convert_audio(
    audioFile: UploadFile = File(...),
    topic: str = Form(...),
    speaker: str = Form(default="Unknown"),
):
    title = f"{topic}{os.environ['TITLE_SUFFIX']}"

    if not audioFile.filename:
        raise HTTPException(status_code=400, detail="Audio file required")

    tmpdir = tempfile.mkdtemp()
    logger.debug(f"Created temp directory: {tmpdir}")
    try:
        audio_in = os.path.join(tmpdir, "input")
        mp3_out = os.path.join(tmpdir, "output.mp3")

        file.save_upload_file(audioFile, audio_in)
        logger.debug(f"Saved audio to {audio_in}, size: {os.path.getsize(audio_in)} bytes")

        cover_in = file.resolve_cover_path(tmpdir)

        mp3.convert_to_mp3(audio_in, mp3_out)

        cover_mime = file.guess_cover_mime("./media/default_cover.jpg")
        mp3.write_id3_tags(
            mp3_out,
            title=title,
            album=os.environ['ALBUM'],
            album_artist=os.environ['ALBUM_ARTIST'],
            artist=speaker,
            year=str(datetime.now().year),
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

# needs to be mounted last, so /api/convert can return 200
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
