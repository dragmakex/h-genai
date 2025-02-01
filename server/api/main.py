import logging
import sys
import traceback

import uvicorn
from fastapi import FastAPI, Request
from mangum import Mangum

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="H-GenAI API", description="REST API for H-GenAI", version="1.0.0")


# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(
            f"Request completed: {request.method} {request.url} - Status: {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url}")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(sys.exc_info()[2]))}")
        raise


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "H-GenAI API is running"}


@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}


# Handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
