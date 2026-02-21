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


### Setup
Do one of the following options to start the app.
Then open http://localhost:8000 in your browser to use it.

Requirements:

- docker

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Option 2: Start Script With Plain Docker
```bash
./start.sh
```

## Configuration

### Environment Variables

The application can be configured using environment variables or a `.env` file. Environment variables take precedence over `.env` file values.

| Key | Required | Description | Example Value |
|----------|----------|-------------|---------|
| `ALBUM` | Yes | Album name for ID3 tags | `"My Podcast"` |
| `GENRE` | Yes | Genre for ID3 tags | `"Podcast"` |
| `TITLE_SUFFIX` | Yes | Suffix appended to episode titles | `" - My Show"` |

those can be passed using 

- `docker-compose.yml` > environment
- `docker run -e Key=Value -e AnotherKey=AnotherValue ...` 
- `.env` file in the project root. 

### Files

Mount or copy files into `/tmp/secrets/`:

- Cover image: `cover.*` contains a base64 encoded image or binary image to be embedded as cover image into the audio files.


## Troubleshooting

**FFmpeg not found**: Ensure FFmpeg is installed with libmp3lame support  
**Large files timeout**: Increase timeout in `_run_ffmpeg()` function  
**Cover art not showing**: Verify image is JPEG or PNG format  
**CORS errors**: Check that CORS middleware is properly configured in backend

## License
MIT
