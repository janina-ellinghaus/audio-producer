# Audio Producer

Convert audio files to MP3 with ID3 tags and cover art.

## Features

- Upload any audio file format
- Convert to high-quality MP3
- Add ID3v2.3 tags (title, album, artist, year, track, genre)
- Embed cover art
- Automatic download of converted file

## Quick Start

### Using Docker

```bash
docker build -t audio-producer .
docker run -p 8000:8000 audio-producer
```

Then open http://localhost:8000 in your browser.

### Local Development

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend (for development, serve the HTML file):
```bash
cd frontend
python -m http.server 8080
```

## API Endpoint

**POST** `/api/convert`

Content-Type: `multipart/form-data`

Fields:
- `audio` (file, required): Audio file to convert
- `cover` (file, required): Cover art image (JPEG/PNG)
- `title` (string, required): Song title
- `album` (string, required): Album name
- `artist` (string, optional): Artist name
- `year` (string, optional): Release year
- `track` (string, optional): Track number
- `genre` (string, optional): Genre

Returns: MP3 file with embedded tags and cover art

## Technology Stack

- **Backend**: Python 3.11, FastAPI, FFmpeg, Mutagen
- **Frontend**: Vue 3 (CDN)
- **Deployment**: Docker

## Requirements

- FFmpeg with libmp3lame support
- Python 3.11+
