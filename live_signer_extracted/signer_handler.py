import os
import json
import boto3
from botocore.config import Config

INPUT_BUCKET = os.environ.get('INPUT_BUCKET')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')

s3_client = boto3.client(
    's3',
    region_name=REGION,
    config=Config(signature_version='s3v4')
)

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

    # Handle CORS pre-flight
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "ok"})}

    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename')
        content_type = body.get('contentType', 'image/jpeg')

        if not filename:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "filename required"})}

        # Base name for outputs
        base_name = os.path.splitext(filename)[0]

        # Generate Pre-Signed S3 Upload URL (valid for 300 seconds)
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': INPUT_BUCKET,
                'Key': filename,
                'ContentType': content_type
            },
            ExpiresIn=300
        )

        # Expected output URLs from the output bucket
        results = {
            "uploadUrl": presigned_url,
            "filename": filename,
            "expectedAssets": {
                "square": f"https://{OUTPUT_BUCKET}.s3.{REGION}.amazonaws.com/processed/square/{base_name}_square.jpg",
                "story": f"https://{OUTPUT_BUCKET}.s3.{REGION}.amazonaws.com/processed/stories/{base_name}_story.jpg",
                "banner": f"https://{OUTPUT_BUCKET}.s3.{REGION}.amazonaws.com/processed/banners/{base_name}_banner.jpg"
            }
        }

        return {"statusCode": 200, "headers": headers, "body": json.dumps(results)}

    except Exception as e:
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}