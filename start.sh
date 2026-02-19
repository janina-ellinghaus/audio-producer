#!/bin/bash

echo "Starting Audio Producer..."
echo "Building Docker image..."
docker build -t audio-producer .

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Starting container on localhost:8000..."
    docker run --rm -p 8000:8000 audio-producer
else
    echo "Build failed!"
    exit 1
fi
