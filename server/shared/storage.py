# shared/storage.py
from dotenv import load_dotenv

import boto3
import os
from botocore.exceptions import ClientError

load_dotenv()

IS_LOCAL = os.getenv('ENV', 'local') == 'local'
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "MINIO_ACCESS_KEY")
MINIO_SECRET_KEY= os.getenv("MINIO_SECRET_KEY", "MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "MINIO_BUCKET")
MINIO_REGION_NAME = os.getenv("MINIO_REGION_NAME", "MINIO_REGION_NAME")

class StorageManager:
    def __init__(self):
        # These would come from your .env file 
        self.endpoint = MINIO_ENDPOINT
        self.access_key = MINIO_ACCESS_KEY
        self.secret_key = MINIO_SECRET_KEY
        self.bucket_name = MINIO_BUCKET

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="us-east-1"
        )

    def upload_file(self, file_obj, object_name):
        """Uploads a file-like object to MinIO/S3"""
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, object_name)
            return True
        except ClientError as e:
            print(f"Storage Upload Error: {e}")
            return False

    def download_file(self, object_name, destination):
        """Downloads a file from MinIO/S3 to a local path"""

        print("\n" + "="*50)
        print(f"[STORAGE DEBUG] Target Endpoint:  {self.endpoint}")
        print(f"[STORAGE DEBUG] Target Bucket:    {self.bucket_name}")
        print(f"[STORAGE DEBUG] Target Object Key: {object_name}")
        print("="*50 + "\n")
        try:
            self.client.download_file(self.bucket_name, object_name, destination)
            return True
        except ClientError as e:
            print(f"Storage Download Error: {e}")
            return False

    def delete_file(self, object_name):
        """Cleans up the file after job completion"""
        self.client.delete_object(Bucket=self.bucket_name, Key=object_name)