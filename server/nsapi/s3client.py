from dotenv import load_dotenv
import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from shared.logger import log_event

load_dotenv()

IS_LOCAL = os.getenv('ENV', 'local') == 'local'
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY= os.getenv("MINIO_SECRET_KEY")
MINIO_REGION_NAME = os.getenv("MINIO_REGION_NAME")


def get_s3_client():

    s3_config = Config(signature_version='s3v4', s3={'addressing_style': 'path'})

    if IS_LOCAL: 
        # local MinIO
        return boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name=MINIO_REGION_NAME,          # MinIO ignores region, but boto3 requires it
            config=s3_config,
        )
    else: 
        # Production AWS (automatically grabs IAM role credentials on EC2)
        return boto3.client('s3', region_name=MINIO_REGION_NAME)
    


def generate_presigned_s3_url(job_id: str, bucket_name: str, object_name: str, expiration=300):
    
    s3_client = get_s3_client()

    try:
        response = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:

        error_code = e.response['Error']['Code']
        if error_code == '404':
            log_event(
                job_id=job_id, 
                message=f"[nsserver] Error: '{bucket_name}' WAS MISSING! Auto-creating it now..."
            )
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            log_event(
                job_id=job_id,
                message=f"[nsserver] Error: '{bucket_name}' S3 Connection error: {e}"
            )
        return None