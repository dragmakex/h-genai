#!/bin/bash

# Exit on error
set -e

# Build the Docker image
echo "Building Docker image..."
docker build -t h-genai-server:local .

# Run the tests
echo "Running tests..."
python3 tests/test_local_lambda.py 