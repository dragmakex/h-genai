import json
import logging
import sys
import traceback
import uuid
import boto3
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from weasyprint import HTML, CSS
from mangum import Mangum
from typing import Dict, Any, List, Optional

from agent.orchestrator import Orchestrator

# Configure DynamoDB
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table('h-genai-jobs')

# Configure S3
s3 = boto3.client('s3')
S3_BUCKET = 'h-genai-pdfs'  # Make sure to create this bucket

# Configure SQS
sqs = boto3.client('sqs')
PDF_GENERATION_QUEUE_URL = 'https://sqs.us-west-2.amazonaws.com/140023381458/h-genai-pdf-generation'

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    pdf_url: Optional[str] = None
    error: Optional[str] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="H-GenAI API", description="REST API for H-GenAI", version="1.0.0")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="template")

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


class CityModel(BaseModel):
    siren: str
    municipality_name: str
    municipality_code: str
    inter_municipality_name: str
    inter_municipality_code: str
    reference_sirens: List[str]
    

@app.post("/generate-pdf", response_model=JobResponse)
async def generate_pdf_from_data(request: Request, city_info: CityModel):
    logger.info("PDF generation endpoint called")
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Create a job record in DynamoDB
        jobs_table.put_item(
            Item={
                'job_id': job_id,
                'status': JobStatus.PENDING.value,
                'created_at': datetime.utcnow().isoformat(),
                'city_info': city_info.dict()
            }
        )
        
        # Send message to SQS
        message_body = {
            'job_id': job_id,
            'city_info': city_info.dict()
        }
        
        sqs.send_message(
            QueueUrl=PDF_GENERATION_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        
        logger.info(f"Job {job_id} created and queued for processing")
        
        # Return the job ID immediately
        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(sys.exc_info()[2]))}")
        
        # Update job status to failed if we managed to create it
        try:
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, error = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': JobStatus.FAILED.value,
                    ':error': str(e)
                }
            )
        except:
            pass
            
        raise HTTPException(status_code=500, detail="Failed to create PDF generation job")

@app.get("/pdf-status/{job_id}", response_model=JobResponse)
async def get_pdf_status(job_id: str):
    """Get the status of a PDF generation job"""
    try:
        response = jobs_table.get_item(Key={'job_id': job_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Job not found")
            
        job = response['Item']
        
        # If the job is completed and we have a PDF URL that's expired, generate a new one
        if job['status'] == JobStatus.COMPLETED.value and 'pdf_url' in job:
            pdf_key = f'pdfs/{job_id}.pdf'
            pdf_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': pdf_key},
                ExpiresIn=3600
            )
            job['pdf_url'] = pdf_url
            
        return JobResponse(
            job_id=job['job_id'],
            status=JobStatus(job['status']),
            pdf_url=job.get('pdf_url'),
            error=job.get('error')
        )
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving job status")

@app.post("/small-generate-pdf")
async def small_generate_pdf_from_data(request: Request, city_info: CityModel):
    logger.info("PDF generation endpoint called")

    orchestrator_instance = Orchestrator(city_info)
    data = orchestrator_instance.test_process_all_sections()

    print(data)

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


@app.post("/test-generate-pdf")
def generate_test_pdf(request: Request):
    """
    This is a test endpoint to return response.pdf
    """
    with open("api/response.pdf", "rb") as pdf_file:
        pdf_data = pdf_file.read()
    return Response(pdf_data, media_type="application/pdf")


# Handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
