# shared/storage.py
import boto3
import os
from botocore.exceptions import ClientError


class StorageManager:
    def __init__(self):
        # These would come from your .env file
        self.endpoint = os.getenv("S3_ENDPOINT", "http://storage:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("S3_SECRET_KEY", "minioadminpassword")
        self.bucket_name = os.getenv("S3_BUCKET", "ns-storage-bucket")

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