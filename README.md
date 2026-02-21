# Audio Producer

## Warning ⚠️

Potentially bad maintained, vibe coding project for the devs personal use ahead!

## Purpose
A web service that accepts audio file uploads, converts them to high-quality MP3 format, adds ID3 tags with metadata, and returns the file for download.

## Features
✨ **Audio Conversion**: Converts any audio format to MP3 using FFmpeg with libmp3lame  
🏷️ **ID3v2.3 Tags**: Embeds title, album, artist, year, track, and genre  
🎨 **Cover Art**: Embeds album artwork (JPEG/PNG) into MP3 files  
📥 **Automatic Download**: Browser automatically downloads the converted file  
🐳 **Docker Ready**: Single command deployment with Docker

## Stack
- **Backend**: Python 3.11, FastAPI, FFmpeg, Mutagen
- **Frontend**: Vue 3 (CDN-based, no build step required)
- **Deployment**: Docker + docker-compose

## Quick Start

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Option 2: Start Script
```bash
./start.sh
```

### Option 3: Manual Docker
```bash
docker build -t audio-producer .
docker run -p 8000:8000 audio-producer
```

Then open **http://localhost:8000** in your browser.

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
The frontend is a single HTML file. To serve it separately:
```bash
cd frontend
python -m http.server 8080
```

## Project Structure
```
.
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Vue.js frontend
├── Dockerfile               # Container definition
├── docker-compose.yml       # Compose configuration
├── start.sh                 # Quick start script
└── README.md                # This file
```

## API Documentation

### Endpoint: POST /api/convert

**Request**: multipart/form-data

| Field   | Type   | Required | Description                    |
|---------|--------|----------|--------------------------------|
| audio   | file   | Yes      | Audio file (any format)        |
| cover   | file   | Yes      | Cover art (JPEG/PNG)           |
| title   | string | Yes      | Song title                     |
| album   | string | Yes      | Album name                     |
| artist  | string | No       | Artist name                    |
| year    | string | No       | Release year                   |
| track   | string | No       | Track number (e.g., "1" or "1/12") |
| genre   | string | No       | Genre                          |

**Response**: audio/mpeg file with Content-Disposition: attachment

## Technical Details

### Audio Conversion
- Uses FFmpeg with `-c:a libmp3lame -q:a 2` for high-quality VBR encoding
- Strips video streams with `-vn` flag
- Processes files in temporary directories with automatic cleanup

### ID3 Tagging
- Uses Mutagen library for reliable ID3v2.3 tag writing
- Embeds cover art as attached picture (APIC frame)
- UTF-8 encoding for international character support

### Security & Robustness
- Validates file uploads and enforces limits
- Sanitizes filenames to prevent path traversal
- 60-second timeout on FFmpeg operations
- Automatic cleanup of temporary files
- CORS enabled for frontend integration

## Requirements
- Docker (for containerized deployment)
- OR: Python 3.11+, FFmpeg with libmp3lame (for local development)

## Configuration

### Environment Variables

The application can be configured using environment variables or a `.env` file. Environment variables take precedence over `.env` file values.

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ALBUM` | Yes | Album name for ID3 tags | `"My Podcast"` |
| `GENRE` | Yes | Genre for ID3 tags | `"Podcast"` |
| `TITLE_SUFFIX` | Yes | Suffix appended to episode titles | `" - My Show"` |

**Example with Docker Compose:**
```yaml
environment:
  - ALBUM=My Podcast Album
  - GENRE=Podcast
  - TITLE_SUFFIX= - My Show
```

**Example with Docker run:**
```bash
docker run -p 8000:8000 \
  -e ALBUM="My Podcast" \
  -e GENRE="Podcast" \
  -e TITLE_SUFFIX=" - My Show" \
  audio-producer
```

**Example with .env file:**
Create a `.env` file in the project root:
```
ALBUM=My Podcast
GENRE=Podcast
TITLE_SUFFIX= - My Show
```

### Port Configuration
The application runs on port 8000 by default. To change:
- Docker: Modify port mapping in `docker-compose.yml` or `docker run` command
- Local: Use `--port` flag with uvicorn

## Troubleshooting

**FFmpeg not found**: Ensure FFmpeg is installed with libmp3lame support  
**Large files timeout**: Increase timeout in `_run_ffmpeg()` function  
**Cover art not showing**: Verify image is JPEG or PNG format  
**CORS errors**: Check that CORS middleware is properly configured in backend

## License
MIT
