# H-GenAI Server

This is the server component of the H-GenAI project, built with FastAPI and AWS Lambda.

## Local Development and Testing

### Prerequisites

- Python 3.11
- Poetry
- Docker
- AWS credentials for Bedrock
- API keys for Serper and Perplexity

### Environment Setup

1. Create a `.env` file in the root directory with the following variables:
```bash
BR_AWS_ACCESS_KEY_ID=your_bedrock_access_key
BR_AWS_SECRET_ACCESS_KEY=your_bedrock_secret_key
BR_AWS_DEFAULT_REGION=us-west-2
SERPERDEV_API_KEY=your_serper_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

2. Install dependencies:
```bash
poetry install
```

### Local Testing with Docker

#### Method 1: Manual Testing

1. Build the Docker image:
```bash
docker build -t h-genai-server:local .
```

2. Run the container with required environment variables:
```bash
docker run -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID=${BR_AWS_ACCESS_KEY_ID} \
  -e AWS_SECRET_ACCESS_KEY=${BR_AWS_SECRET_ACCESS_KEY} \
  -e AWS_DEFAULT_REGION=us-west-2 \
  -e BR_AWS_ACCESS_KEY_ID=${BR_AWS_ACCESS_KEY_ID} \
  -e BR_AWS_SECRET_ACCESS_KEY=${BR_AWS_SECRET_ACCESS_KEY} \
  -e BR_AWS_DEFAULT_REGION=us-west-2 \
  -e SERPERDEV_API_KEY=${SERPERDEV_API_KEY} \
  -e PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY} \
  h-genai-server:local
```

3. Test the endpoints using curl:
```bash
# Health check
curl -X POST "http://localhost:8080/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "routeKey": "GET /",
    "rawPath": "/",
    "requestContext": {
      "http": {
        "method": "GET",
        "path": "/"
      }
    }
  }'

# Process document
curl -X POST "http://localhost:8080/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "routeKey": "POST /process",
    "rawPath": "/process",
    "requestContext": {
      "http": {
        "method": "POST",
        "path": "/process"
      }
    },
    "body": "{\"text\":\"What is the capital of France?\",\"context\":\"France is a country in Western Europe. Its capital is Paris.\"}"
  }'
```

#### Method 2: Automated Testing

We provide a test script that automates the testing process:

1. Make the test script executable:
```bash
chmod +x test_local.sh
```

2. Run the tests:
```bash
./test_local.sh
```

The test script will:
- Build the Docker image
- Start a container with the required environment variables
- Run a series of test cases
- Show detailed results for each test
- Display a summary of passed/failed tests
- Clean up by stopping and removing the container

### Adding New Test Cases

To add new test cases, edit `tests/test_local_lambda.py` and add to the `test_cases` list:

```python
test_cases = [
    TestCase(
        name="Your Test Name",
        method="POST",  # or GET, PUT, etc.
        path="/your-endpoint",
        body={  # Optional, for POST requests
            "key": "value"
        },
        expected_status=200,
        description="Description of what this test does"
    ),
]
```

### Troubleshooting

1. Platform Mismatch Warning:
   - If you see a warning about platform mismatch (amd64 vs arm64), it's normal on M1/M2 Macs
   - The container will still work as expected

2. Environment Variables:
   - Make sure all required environment variables are set in your `.env` file
   - Both AWS and Bedrock credentials are required
   - Check that API keys for Serper and Perplexity are valid

3. Common Errors:
   - "BR_AWS_ACCESS_KEY_ID is not set": Check your environment variables
   - "Could not connect to Amazon Bedrock": Verify AWS/Bedrock credentials
   - "The adapter was unable to infer a handler": Make sure the API Gateway event format is correct

### Cleaning Up

To stop and remove the container:
```bash
docker ps | grep h-genai-server:local | awk '{print $1}' | xargs docker stop
docker ps -a | grep h-genai-server:local | awk '{print $1}' | xargs docker rm
```