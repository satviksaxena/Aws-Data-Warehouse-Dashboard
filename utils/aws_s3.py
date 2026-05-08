import os
import boto3
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self, region_name='us-east-1'):
        # Will use credentials from environment or AWS config
        self.s3_client = boto3.client('s3', region_name=region_name)
        
    def upload_file(self, file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket"""
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.s3_client.upload_file(file_name, bucket, object_name)
            logger.info(f"Successfully uploaded {file_name} to s3://{bucket}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(self, bucket, object_name, file_name):
        """Download a file from an S3 bucket"""
        try:
            self.s3_client.download_file(bucket, object_name, file_name)
            logger.info(f"Successfully downloaded s3://{bucket}/{object_name} to {file_name}")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file: {e}")
            return False
            
    def list_files(self, bucket, prefix=''):
        """List files in an S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            return []
