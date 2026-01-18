"""
S3 Storage Service

Handles temporary photo storage
"""

import boto3
from botocore.exceptions import ClientError
import logging
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class S3Storage:
    """
    S3-compatible storage (MinIO or AWS S3)
    """

    def __init__(self):
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.debug(f"Bucket {self.bucket} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"Creating bucket: {self.bucket}")
                self.s3_client.create_bucket(Bucket=self.bucket)
            else:
                logger.error(f"Error checking bucket: {e}")

    async def upload(self, data: bytes, key: str) -> str:
        """
        Upload file to S3

        Args:
            data: File bytes
            key: S3 object key

        Returns:
            S3 object URL
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType='image/jpeg'
            )

            logger.debug(f"Uploaded to S3: {key}")

            return f"s3://{self.bucket}/{key}"

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def download(self, key: str) -> bytes:
        """
        Download file from S3

        Args:
            key: S3 object key

        Returns:
            File bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )

            data = response['Body'].read()

            logger.debug(f"Downloaded from S3: {key} ({len(data)} bytes)")

            return data

        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise

    async def delete(self, key: str):
        """
        Delete file from S3

        Args:
            key: S3 object key
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )

            logger.debug(f"Deleted from S3: {key}")

        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            raise

    async def get_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for download

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
