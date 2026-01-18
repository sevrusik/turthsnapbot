"""
Visual Watermark Detector

Detects text-based watermarks on images using OCR (Optical Character Recognition).
Identifies watermarks from AI generators like Google Gemini, DALL-E, Midjourney, etc.
"""

import logging
from typing import Dict, List, Optional
from PIL import Image
import io
import re

logger = logging.getLogger(__name__)


class VisualWatermarkDetector:
    """
    Detects visible text watermarks on images using Tesseract OCR
    """

    # Known AI generator watermarks (case-insensitive)
    AI_WATERMARKS = {
        'google': ['google', 'gemini', 'bard', 'imagen'],
        'openai': ['openai', 'dall-e', 'dalle', 'chatgpt'],
        'midjourney': ['midjourney', 'mj'],
        'stable_diffusion': ['stable diffusion', 'stability ai', 'stabilityai'],
        'adobe': ['adobe firefly', 'firefly'],
        'canva': ['canva', 'magic media'],
        'craiyon': ['craiyon', 'dall-e mini'],
        'nightcafe': ['nightcafe'],
        'artbreeder': ['artbreeder'],
        'deepai': ['deepai', 'deep ai'],
    }

    # Stock photo watermarks
    STOCK_WATERMARKS = {
        'shutterstock': ['shutterstock'],
        'getty': ['getty images', 'gettyimages'],
        'istock': ['istock'],
        'adobe_stock': ['adobe stock'],
        'freepik': ['freepik'],
        'pexels': ['pexels'],
        'unsplash': ['unsplash'],
        'pixabay': ['pixabay'],
    }

    def __init__(self):
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available"""
        try:
            import pytesseract
            # Try to get version to verify it works
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
            return False

    def detect_watermark(self, image_path: str) -> Dict:
        """
        Detect visible watermarks using OCR (synchronous version for file path)

        Args:
            image_path: Path to image file

        Returns:
            {
                "has_watermark": bool,
                "watermark_type": str,
                "provider": str,
                "confidence": float,
                "text_found": str,
                "location": str,
                "method": str
            }
        """

        if not self.tesseract_available:
            return {
                "has_watermark": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": "",
                "details": {"error": "Tesseract OCR not available"}
            }

        try:
            import pytesseract

            # Open image from path
            image = Image.open(image_path)

            # Convert MPO (iPhone) to standard format if needed
            if image.format == 'MPO':
                # MPO images have multiple frames, use the first one
                logger.info("🔄 Converting MPO format to JPEG for OCR")
                image.seek(0)  # Use first frame

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Perform OCR
            logger.info(f"🔍 Running OCR watermark detection on {image.size} image")

            # Extract text with confidence scores
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 11'  # Sparse text detection
            )

            # Combine all detected text
            all_text = ' '.join([
                str(text).lower()
                for text, conf in zip(ocr_data['text'], ocr_data['conf'])
                if conf > 30 and text.strip()  # Filter low confidence
            ])

            logger.info(f"📝 OCR extracted text: '{all_text[:200]}'")

            # Check for AI generator watermarks
            for provider, keywords in self.AI_WATERMARKS.items():
                for keyword in keywords:
                    if keyword in all_text:
                        logger.info(f"🎯 AI watermark found: {provider} - '{keyword}'")
                        return {
                            "has_watermark": True,
                            "watermark_type": provider.replace('_', ' ').title(),
                            "provider": provider,
                            "confidence": 0.90,
                            "text_found": keyword,
                            "location": "bottom_right",  # Default location
                            "method": "ocr_text_detection",
                            "details": {
                                "full_text": all_text[:500],
                                "detection_method": "tesseract_ocr"
                            }
                        }

            # Check for stock photo watermarks
            for provider, keywords in self.STOCK_WATERMARKS.items():
                for keyword in keywords:
                    if keyword in all_text:
                        logger.info(f"📸 Stock photo watermark found: {provider} - '{keyword}'")
                        return {
                            "has_watermark": True,
                            "watermark_type": "stock_photo",
                            "provider": provider,
                            "confidence": 0.85,
                            "text_found": keyword,
                            "location": "center",
                            "method": "ocr_text_detection",
                            "details": {
                                "full_text": all_text[:500],
                                "detection_method": "tesseract_ocr"
                            }
                        }

            # No watermark found
            logger.info("🔍 No watermark text detected via OCR")
            return {
                "has_watermark": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": ""
            }

        except Exception as e:
            logger.error(f"❌ OCR watermark detection error: {e}", exc_info=True)
            return {
                "has_watermark": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": "",
                "details": {"error": str(e)}
            }

    async def detect(self, image_bytes: bytes) -> Dict:
        """
        Detect visible watermarks using OCR (async version for bytes)

        Args:
            image_bytes: Image binary data

        Returns:
            {
                "detected": bool,
                "watermark_type": str,  # "ai_generator", "stock_photo", "other"
                "provider": str,  # e.g., "google", "shutterstock"
                "confidence": float,
                "text_found": str,
                "details": {}
            }
        """

        if not self.tesseract_available:
            return {
                "detected": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": "",
                "details": {"error": "Tesseract OCR not available"}
            }

        try:
            import pytesseract

            # Open image
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Perform OCR
            logger.info(f"Running OCR on image {image.size}")

            # Extract text with confidence scores
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 11'  # Sparse text detection
            )

            # Combine all detected text
            all_text = ' '.join([
                str(text).lower()
                for text, conf in zip(ocr_data['text'], ocr_data['conf'])
                if conf > 30 and text.strip()  # Filter low confidence
            ])

            logger.info(f"OCR extracted text: {all_text[:200]}")

            # Check for AI generator watermarks
            for provider, keywords in self.AI_WATERMARKS.items():
                for keyword in keywords:
                    if keyword in all_text:
                        return {
                            "detected": True,
                            "watermark_type": "ai_generator",
                            "provider": provider,
                            "confidence": 0.95,
                            "text_found": keyword,
                            "details": {
                                "full_text": all_text[:500],
                                "detection_method": "ocr"
                            }
                        }

            # Check for stock photo watermarks
            for provider, keywords in self.STOCK_WATERMARKS.items():
                for keyword in keywords:
                    if keyword in all_text:
                        return {
                            "detected": True,
                            "watermark_type": "stock_photo",
                            "provider": provider,
                            "confidence": 0.90,
                            "text_found": keyword,
                            "details": {
                                "full_text": all_text[:500],
                                "detection_method": "ocr"
                            }
                        }

            # No watermark detected
            return {
                "detected": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": "",
                "details": {
                    "full_text": all_text[:500] if all_text else "",
                    "detection_method": "ocr"
                }
            }

        except Exception as e:
            logger.error(f"Visual watermark detection failed: {e}", exc_info=True)
            return {
                "detected": False,
                "watermark_type": None,
                "provider": None,
                "confidence": 0.0,
                "text_found": "",
                "details": {"error": str(e)}
            }

    async def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract all text from image (utility method)

        Args:
            image_bytes: Image binary data

        Returns:
            Extracted text string
        """
        if not self.tesseract_available:
            return ""

        try:
            import pytesseract

            image = Image.open(io.BytesIO(image_bytes))

            if image.mode != 'RGB':
                image = image.convert('RGB')

            text = pytesseract.image_to_string(image, config='--psm 11')
            return text.strip()

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
