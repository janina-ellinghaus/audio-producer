"""
Test suite for the Audio Producer API.
Tests verify that audio conversion, metadata embedding, and file handling work correctly.
"""

import pytest
import io
import tempfile
import wave
import struct

from starlette.testclient import TestClient
from mutagen.id3 import ID3
from mutagen.mp3 import MP3

from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    # Use positional argument for starlette.testclient.TestClient
    return TestClient(app)


@pytest.fixture
def test_audio_file():
    """Generate a minimal WAV test audio file (1 second)"""
    sample_rate = 44100
    duration = 1
    frequency = 1000
    
    frames = []
    for i in range(sample_rate * duration):
        # Simple sine-like wave
        sample = int(32767 * 0.5 * (i % (sample_rate // frequency) / (sample_rate // frequency)))
        frames.append(struct.pack('<h', sample))
    
    # Create BytesIO WAV file
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    wav_buffer.seek(0)
    return wav_buffer


@pytest.fixture
def test_cover_image():
    """Generate a minimal JPEG cover image (1x1 pixel)"""
    try:
        from PIL import Image
        img = Image.new('RGB', (1, 1), color='red')
        cover_buffer = io.BytesIO()
        img.save(cover_buffer, 'JPEG')
        cover_buffer.seek(0)
        return cover_buffer
    except ImportError:
        # Fallback: minimal JPEG binary if PIL not available
        # This is a real minimal 1x1 red JPEG
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD4, 0xFF, 0xD9
        ])
        return io.BytesIO(jpeg_bytes)


class TestMinimalConversion:
    """Test basic audio conversion with minimal required fields"""
    
    def test_convert_with_required_fields_only(self, client, test_audio_file, test_cover_image):
        """Test conversion with title and album (required fields)"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test Song",
                "album": "Test Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert len(response.content) > 0
        
        # Verify it's a valid MP3
        mp3_buffer = io.BytesIO(response.content)
        mp3 = MP3(mp3_buffer)
        assert mp3.info.length > 0


class TestMetadataEmbedding:
    """Test that metadata is correctly embedded in MP3 files"""
    
    def test_title_and_album_embedded(self, client, test_audio_file, test_cover_image):
        """Test that title and album are embedded"""
        response = client.post(
            "/api/convert",
            data={
                "title": "My Song",
                "album": "My Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        
        # Verify metadata
        mp3_buffer = io.BytesIO(response.content)
        tags = ID3(mp3_buffer)
        
        assert str(tags.get("TIT2")) == "My Song"
        assert str(tags.get("TALB")) == "My Album"
    
    def test_all_optional_fields_embedded(self, client, test_audio_file, test_cover_image):
        """Test that all optional fields are correctly embedded"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Complete Test",
                "album": "My Album",
                "artist": "Test Artist",
                "year": "2026",
                "track": "5",
                "genre": "Electronic",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        
        # Verify all metadata
        mp3_buffer = io.BytesIO(response.content)
        tags = ID3(mp3_buffer)
        
        assert str(tags.get("TIT2")) == "Complete Test"
        assert str(tags.get("TALB")) == "My Album"
        assert str(tags.get("TPE1")) == "Test Artist"
        assert str(tags.get("TDRC")) == "2026"
        assert str(tags.get("TRCK")) == "5"
        assert str(tags.get("TCON")) == "Electronic"
    
    def test_default_artist_when_not_provided(self, client, test_audio_file, test_cover_image):
        """Test that default artist is used when not provided"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Song",
                "album": "Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        
        mp3_buffer = io.BytesIO(response.content)
        tags = ID3(mp3_buffer)
        
        assert str(tags.get("TPE1")) == "Unknown Artist"


class TestCoverArtEmbedding:
    """Test that cover art is correctly embedded"""
    
    def test_cover_art_embedded(self, client, test_audio_file, test_cover_image):
        """Test that cover art is embedded as APIC frame"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Song with Cover",
                "album": "Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        
        mp3_buffer = io.BytesIO(response.content)
        tags = ID3(mp3_buffer)
        
        # Check that cover art is present
        assert tags.get("APIC:Cover") is not None
        assert tags.get("APIC:Cover").mime == "image/jpeg"


class TestOutputFormat:
    """Test output file format and properties"""
    
    def test_output_is_valid_mp3(self, client, test_audio_file, test_cover_image):
        """Test that output is a valid MP3 file"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test",
                "album": "Test",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        
        # Verify it starts with MP3 magic bytes or ID3 header
        content = response.content
        is_id3 = content[:3] == b'ID3'
        is_mp3 = content[:2] == b'\xFF\xFB' or content[:2] == b'\xFF\xFA'
        assert is_id3 or is_mp3, "File is not a valid MP3"
    
    def test_download_filename(self, client, test_audio_file, test_cover_image):
        """Test that download filename is correctly set"""
        response = client.post(
            "/api/convert",
            data={
                "title": "My Song Title",
                "album": "Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "My Song Title.mp3" in disposition


class TestErrorHandling:
    """Test error handling for invalid inputs"""
    
    def test_missing_audio_file(self, client, test_cover_image):
        """Test that missing audio file returns 400 error"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test",
                "album": "Test",
            },
            files={
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 422  # Unprocessable entity (missing file)
    
    def test_missing_cover_image(self, client, test_audio_file):
        """Test that missing cover image returns 400 error"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test",
                "album": "Test",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
            }
        )
        
        assert response.status_code == 422  # Unprocessable entity (missing file)
    
    def test_missing_title(self, client, test_audio_file, test_cover_image):
        """Test that missing title returns 422 error"""
        response = client.post(
            "/api/convert",
            data={
                "album": "Test",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 422  # Unprocessable entity (missing field)
    
    def test_missing_album(self, client, test_audio_file, test_cover_image):
        """Test that missing album returns 422 error"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 422  # Unprocessable entity (missing field)


class TestFileNaming:
    """Test filename sanitization and handling"""
    
    def test_special_characters_in_title(self, client, test_audio_file, test_cover_image):
        """Test that special characters in title are sanitized"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Song: With/Special\\Characters?!",
                "album": "Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        # Should have sanitized filename without problematic characters
        assert ".mp3" in disposition
        assert "?" not in disposition
    
    def test_empty_title_uses_default(self, client, test_audio_file, test_cover_image):
        """Test that empty title uses default 'output'"""
        response = client.post(
            "/api/convert",
            data={
                "title": "   ",  # Whitespace only
                "album": "Album",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "output.mp3" in disposition


class TestAudioQuality:
    """Test audio quality and conversion parameters"""
    
    def test_mp3_bitrate_reasonable(self, client, test_audio_file, test_cover_image):
        """Test that output MP3 has reasonable bitrate (quality setting 2)"""
        response = client.post(
            "/api/convert",
            data={
                "title": "Test",
                "album": "Test",
            },
            files={
                "audio": ("test.wav", test_audio_file, "audio/wav"),
                "cover": ("cover.jpg", test_cover_image, "image/jpeg"),
            }
        )
        
        assert response.status_code == 200
        
        mp3_buffer = io.BytesIO(response.content)
        mp3 = MP3(mp3_buffer)
        
        # Quality 2 typically results in ~128+ kbps
        # Check that bitrate is present and reasonable
        assert mp3.info.bitrate > 0
        assert mp3.info.bitrate < 320000  # Less than 320 kbps


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
