#!/usr/bin/env python3
import json
import os
import subprocess
import time
from typing import Dict, Optional
import requests
from dataclasses import dataclass
import signal

@dataclass
class TestCase:
    name: str
    method: str
    path: str
    body: Optional[Dict] = None
    expected_status: int = 200
    description: str = ""

class LocalLambdaTester:
    def __init__(self, image_name: str = "h-genai-server:local"):
        self.image_name = image_name
        self.container_id = None
        self.base_url = "http://localhost:8080/2015-03-31/functions/function/invocations"
        
    def _create_api_gateway_event(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        event = {
            "version": "2.0",
            "routeKey": f"{method} {path}",
            "rawPath": path,
            "rawQueryString": "",
            "headers": {
                "accept": "*/*",
                "content-type": "application/json",
                "host": "localhost:8080",
                "user-agent": "python-requests/2.31.0"
            },
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "api-id",
                "domainName": "localhost:8080",
                "domainPrefix": "localhost",
                "http": {
                    "method": method,
                    "path": path,
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "python-requests/2.31.0"
                },
                "requestId": "test-request-id",
                "routeKey": f"{method} {path}",
                "stage": "$default",
                "time": "12/Mar/2024:19:03:58 +0000",
                "timeEpoch": 1710270238
            },
            "isBase64Encoded": False
        }
        
        if body:
            event["body"] = json.dumps(body)
            
        return event

    def start_container(self):
        """Start the Lambda container with required environment variables."""
        env_vars = {
            "AWS_ACCESS_KEY_ID": os.getenv("BR_AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("BR_AWS_SECRET_ACCESS_KEY"),
            "AWS_DEFAULT_REGION": "us-west-2",
            "BR_AWS_ACCESS_KEY_ID": os.getenv("BR_AWS_ACCESS_KEY_ID"),
            "BR_AWS_SECRET_ACCESS_KEY": os.getenv("BR_AWS_SECRET_ACCESS_KEY"),
            "BR_AWS_DEFAULT_REGION": "us-west-2",
            "SERPERDEV_API_KEY": os.getenv("SERPERDEV_API_KEY"),
            "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY")
        }
        
        env_args = sum([["-e", f"{k}={v}"] for k, v in env_vars.items() if v], [])
        cmd = ["docker", "run", "-d", "-p", "8080:8080"] + env_args + [self.image_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start container: {result.stderr}")
            
        self.container_id = result.stdout.strip()
        print(f"Container started with ID: {self.container_id}")
        time.sleep(5)  # Wait for the container to initialize

    def stop_container(self):
        """Stop and remove the Lambda container."""
        if self.container_id:
            subprocess.run(["docker", "stop", self.container_id], check=True)
            subprocess.run(["docker", "rm", self.container_id], check=True)
            print(f"Container {self.container_id} stopped and removed")
            self.container_id = None

    def test_endpoint(self, test_case: TestCase) -> bool:
        """Test a specific endpoint with the given test case."""
        print(f"\nTesting: {test_case.name}")
        print(f"Description: {test_case.description}")
        
        event = self._create_api_gateway_event(test_case.method, test_case.path, test_case.body)
        
        try:
            response = requests.post(self.base_url, json=event)
            lambda_response = response.json()
            
            actual_status = lambda_response.get("statusCode", 500)
            success = actual_status == test_case.expected_status
            
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"Expected status: {test_case.expected_status}")
            print(f"Actual status: {actual_status}")
            print("Response:", json.dumps(lambda_response, indent=2))
            
            return success
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            return False

    def run_tests(self, test_cases: list[TestCase]):
        """Run all test cases."""
        try:
            self.start_container()
            
            results = []
            for test_case in test_cases:
                results.append(self.test_endpoint(test_case))
                
            total = len(results)
            passed = sum(results)
            print(f"\nTest Summary:")
            print(f"Total tests: {total}")
            print(f"Passed: {passed}")
            print(f"Failed: {total - passed}")
            
        except KeyboardInterrupt:
            print("\nTests interrupted by user")
        finally:
            self.stop_container()

def main():
    # Define test cases
    test_cases = [
        TestCase(
            name="Health Check",
            method="GET",
            path="/",
            expected_status=200,
            description="Basic health check endpoint"
        ),
        TestCase(
            name="Process Document",
            method="POST",
            path="/process",
            body={
                "text": "What is the capital of France?",
                "context": "France is a country in Western Europe. Its capital is Paris."
            },
            expected_status=200,
            description="Test document processing with simple context"
        ),
        # Add more test cases here
    ]
    
    # Run tests
    tester = LocalLambdaTester()
    tester.run_tests(test_cases)

if __name__ == "__main__":
    main() 