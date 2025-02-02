import json
import logging
import sys
import traceback
import boto3
from datetime import datetime
from weasyprint import HTML, CSS
from fastapi.templating import Jinja2Templates

from agent.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure AWS services
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
jobs_table = dynamodb.Table('h-genai-jobs')
S3_BUCKET = 'h-genai-pdfs'

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="template")

def process_pdf_generation(event, context):
    """
    Lambda function to process PDF generation requests from SQS
    """
    try:
        # Process SQS messages
        for record in event['Records']:
            message_body = json.loads(record['body'])
            job_id = message_body['job_id']
            city_info = message_body['city_info']
            
            try:
                # Update status to processing
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'processing'}
                )
                
                # Generate the PDF
                orchestrator_instance = Orchestrator(city_info)
                data = orchestrator_instance.parallel_process_all_sections()
                
                # Generate HTML
                html_content = templates.TemplateResponse(
                    "index.html",
                    {
                        "request": None,  # Not needed in this context
                        "data": data
                    }
                ).body.decode('utf-8')

                # Read CSS
                with open("template/styles.css", "r") as css_file:
                    css_content = css_file.read()

                # Generate PDF
                css = CSS(string=css_content)
                pdf = HTML(string=html_content, base_url="./template").write_pdf(stylesheets=[css])
                
                # Upload to S3
                pdf_key = f'pdfs/{job_id}.pdf'
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=pdf_key,
                    Body=pdf,
                    ContentType='application/pdf'
                )
                
                # Generate pre-signed URL
                pdf_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': pdf_key},
                    ExpiresIn=3600
                )
                
                # Update job status to completed
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status, pdf_url = :pdf_url',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':pdf_url': pdf_url
                    }
                )
                
                logger.info(f"PDF generation completed for job {job_id}")
                
            except Exception as e:
                logger.error(f"PDF generation failed for job {job_id}: {str(e)}")
                logger.error(f"Traceback: {''.join(traceback.format_tb(sys.exc_info()[2]))}")
                
                # Update job status to failed
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status, error = :error',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':error': str(e)
                    }
                )
                
                # Don't raise the exception - we want to process other messages in the batch if any
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps('PDF generation processing completed')
        }
        
    except Exception as e:
        logger.error(f"Error processing SQS messages: {str(e)}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(sys.exc_info()[2]))}")
        raise 