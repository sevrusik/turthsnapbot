"""
FraudLens API Client

Handles communication with FraudLens detection API
"""

import httpx
from typing import Dict
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class FraudLensClient:
    """
    FraudLens API client

    Provides methods to call FraudLens consumer endpoints
    """

    def __init__(self):
        self.base_url = settings.FRAUDLENS_API_URL
        self.timeout = settings.FRAUDLENS_API_TIMEOUT

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

    async def verify_photo(
        self,
        image_bytes: bytes,
        detail_level: str = "basic",
        preserve_exif: bool = False
    ) -> Dict:
        """
        Verify photo using FraudLens API

        Args:
            image_bytes: Photo binary data
            detail_level: "basic" or "detailed"
            preserve_exif: True if sent as document (EXIF preserved)

        Returns:
            {
                "verdict": "real" | "ai_generated" | "manipulated" | "inconclusive",
                "confidence": 0.95,
                "verdict_reason": "Human-readable explanation",
                "watermark_detected": bool,
                "watermark_analysis": {...},
                "processing_time_ms": 2340,
                "details": {...}
            }

        Raises:
            AnalysisError: If analysis fails
            AnalysisTimeoutError: If analysis takes too long
            AuthenticationError: If API authentication fails
        """

        files = {
            "image": ("photo.jpg", image_bytes, "image/jpeg")
        }

        # Use data (not params) for multipart/form-data
        data = {
            "detail_level": detail_level,
            "preserve_exif": str(preserve_exif).lower()  # FastAPI Form expects string
        }

        try:
            logger.debug(f"Calling FraudLens API: {self.base_url}/api/v1/verify")

            response = await self.client.post(
                "/api/v1/verify",  # Photo verification endpoint
                files=files,
                data=data  # Use data (not params) for Form fields
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"FraudLens response: verdict={result['verdict']}, "
                f"confidence={result['confidence']:.2f}, "
                f"time={result.get('processing_time_ms', 0)}ms"
            )

            return result

        except httpx.TimeoutException as e:
            logger.error(f"FraudLens timeout: {e}")
            raise AnalysisTimeoutError("Analysis took too long. Please try again.")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("FraudLens authentication failed")
                raise AuthenticationError("Invalid API credentials")
            elif e.response.status_code == 429:
                logger.warning("FraudLens rate limit exceeded")
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            else:
                logger.error(f"FraudLens HTTP error: {e.response.status_code} - {e.response.text}")
                raise AnalysisError(f"API error: {e.response.text}")

        except Exception as e:
            logger.error(f"FraudLens unexpected error: {e}", exc_info=True)
            raise AnalysisError(f"Unexpected error: {str(e)}")

    async def generate_pdf_report(
        self,
        image_bytes: bytes,
        preserve_exif: bool = False,
        include_image: bool = True
    ) -> bytes:
        """
        Generate PDF forensic report

        Args:
            image_bytes: Photo binary data
            preserve_exif: True if sent as document (EXIF preserved)
            include_image: Whether to embed image in PDF

        Returns:
            PDF file as bytes

        Raises:
            AnalysisError: If PDF generation fails
        """
        files = {
            "image": ("photo.jpg", image_bytes, "image/jpeg")
        }

        data = {
            "preserve_exif": str(preserve_exif).lower(),
            "include_image": str(include_image).lower()
        }

        try:
            logger.debug(f"Generating PDF report via FraudLens API")

            response = await self.client.post(
                "/api/v1/reports/pdf",
                files=files,
                data=data
            )

            response.raise_for_status()

            # Response is raw PDF bytes
            pdf_bytes = response.content

            logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")

            return pdf_bytes

        except httpx.TimeoutException as e:
            logger.error(f"PDF generation timeout: {e}")
            raise AnalysisTimeoutError("PDF generation took too long. Please try again.")

        except httpx.HTTPStatusError as e:
            logger.error(f"PDF generation HTTP error: {e.response.status_code} - {e.response.text}")
            raise AnalysisError(f"PDF generation failed: {e.response.text}")

        except Exception as e:
            logger.error(f"PDF generation unexpected error: {e}", exc_info=True)
            raise AnalysisError(f"PDF generation error: {str(e)}")

    async def health_check(self) -> Dict:
        """
        Check FraudLens API health

        Returns:
            {"status": "healthy", ...}
        """
        try:
            response = await self.client.get("/api/v1/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"FraudLens health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Custom exceptions
class AnalysisError(Exception):
    """Base analysis error"""
    pass


class AnalysisTimeoutError(AnalysisError):
    """Analysis timeout error"""
    pass


class AuthenticationError(AnalysisError):
    """Authentication error"""
    pass


class RateLimitError(AnalysisError):
    """Rate limit error"""
    pass
