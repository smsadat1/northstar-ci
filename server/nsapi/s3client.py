import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


IS_LOCAL = os.getenv('ENV', 'local') == 'local'
S3_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://storage:9000")


def get_s3_client():

    s3_config = Config(signature_version='s3v4', s3={'addressing_style': 'path'})

    if IS_LOCAL: 
        # local MinIO
        return boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadminpassword",
            region_name="us-east-1", # MinIO ignores region, but boto3 requires it
            config=s3_config,
        )
    else: 
        # Production AWS (automatically grabs IAM role credentials on EC2)
        return boto3.client('s3', region_name='us-east-1')
    


def generate_presigned_s3_url(bucket_name: str, object_name: str, expiration=300):
    
    s3_client = get_s3_client()

    try:
        response = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket_name, 'Key': object_name, 'ContentType': 'application/gzip'},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(f"Error generating MinIO/S3 url: {e}")
        return None