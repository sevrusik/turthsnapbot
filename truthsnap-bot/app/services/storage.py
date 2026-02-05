"""
S3 Storage Service

Handles temporary photo storage using async aioboto3
"""

import aioboto3
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
    S3-compatible storage (MinIO or AWS S3) with async operations

    Uses aioboto3 for non-blocking I/O
    """

    def __init__(self):
        """
        Initialize S3 storage

        Note: Use async context manager or call ensure_bucket() after init
        """
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        self.endpoint_url = settings.S3_ENDPOINT
        self.bucket = settings.S3_BUCKET

    async def ensure_bucket(self):
        """
        Ensure bucket exists (async)

        Call this after initialization or use async context manager
        """
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket)
                logger.debug(f"Bucket {self.bucket} exists")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.info(f"Creating bucket: {self.bucket}")
                    await s3.create_bucket(Bucket=self.bucket)
                else:
                    logger.error(f"Error checking bucket: {e}")
                    raise

    async def upload(self, data: bytes, key: str) -> str:
        """
        Upload file to S3 (async)

        Args:
            data: File bytes
            key: S3 object key

        Returns:
            S3 object URL
        """
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                await s3.put_object(
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
        Download file from S3 (async)

        Args:
            key: S3 object key

        Returns:
            File bytes
        """
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                response = await s3.get_object(
                    Bucket=self.bucket,
                    Key=key
                )

                # Read body asynchronously
                async with response['Body'] as stream:
                    data = await stream.read()

                logger.debug(f"Downloaded from S3: {key} ({len(data)} bytes)")

                return data

        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise

    async def delete(self, key: str):
        """
        Delete file from S3 (async)

        Args:
            key: S3 object key
        """
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                await s3.delete_object(
                    Bucket=self.bucket,
                    Key=key
                )

                logger.debug(f"Deleted from S3: {key}")

        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            raise

    async def get_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for download (async)

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=expiration
                )

                return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
