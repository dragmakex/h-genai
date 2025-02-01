import logging
import sys
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from weasyprint import HTML, CSS
from mangum import Mangum
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="H-GenAI API", description="REST API for H-GenAI", version="1.0.0")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="xtemplate")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://127.0.0.1:5173",
        "https://kbba87ikh5.execute-api.us-west-2.amazonaws.com",
        "https://kbba87ikh5.execute-api.us-west-2.amazonaws.com/*",
        "https://aws-deployment.d5glcpyeyb6n5.amplifyapp.com/*",
        "https://aws-deployment.d5glcpyeyb6n5.amplifyapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

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


@app.post("/generate-pdf")
async def generate_pdf_from_data(request: Request, data: Dict[Any, Any]):
    logger.info("PDF generation endpoint called")
    try:
        html_content = templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "data": data
            }
        ).body.decode('utf-8')

        with open("template/styles.css", "r") as css_file:
            css_content = css_file.read()

        css = CSS(string=css_content)
        pdf = HTML(string=html_content, base_url="./template").write_pdf(stylesheets=[css])

        logger.info("PDF generated successfully")
        return HTMLResponse(pdf, media_type="application/pdf")
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(sys.exc_info()[2]))}")
        raise


# Handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
