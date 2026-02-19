# Audio Producer API Test Suite

14 comprehensive test cases covering audio conversion, metadata embedding, error handling, and file format validation. All tests are organized into functional categories by test class.

## Running the Tests

**Docker (recommended):**
```bash
docker exec $(docker ps | grep audio-producer | awk '{print $1}') \
  bash -c 'cd /app/backend && python -m pytest test_main.py -v'
```

**With coverage report:**
```bash
docker exec $(docker ps | grep audio-producer | awk '{print $1}') \
  bash -c 'cd /app/backend && python -m pytest test_main.py --cov=main --cov-report=term-missing'
```

## How Tests Verify Past Bugs Fixes

### Routing Bug (405 Method Not Allowed)
Tests verify that `/api/convert` POST endpoint returns HTTP 200. If static files were still mounted first, endpoints would return HTTP 405.

### File Handling Bug (Output File Not Found)  
Tests read and validate the returned MP3 files and verify ID3 tags are present. If the temp directory was deleted before streaming, tests would fail with "File not found" errors.

## Troubleshooting

| Issue | Likely Cause |
|-------|-------------|
| Tests fail with "File at path does not exist" | File deletion bug - temp dir deleted before streaming |
| Tests fail with ID3 errors | Metadata embedding failed |
| Tests timeout | FFmpeg conversion taking too long - check system resources |
