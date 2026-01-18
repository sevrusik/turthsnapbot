"""
Core Fraud Detection Engine (Simplified for Consumer API)

This is a simplified version that focuses on AI-generated detection
"""

import asyncio
from typing import Dict
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.integrations.simple_detector import detect_ai_basic

logger = logging.getLogger(__name__)


class FraudDetector:
    """
    Main fraud detection engine

    For consumer API, focuses on:
    - AI generation detection
    - Deepfake detection
    - Basic manipulation detection
    """

    def __init__(self):
        self.enabled = True

    async def detect_ai_generation(self, image_bytes: bytes) -> Dict:
        """
        Detect if image is AI-generated

        Uses heuristic-based detection with 4 real checks:
        1. EXIF metadata presence
        2. Noise pattern analysis
        3. Color distribution
        4. Gradient smoothness

        Args:
            image_bytes: Image binary data

        Returns:
            {
                "ai_score": float,  # 0-1, higher = more likely AI
                "primary_reason": str,
                "checks": [...],
                "ai_signatures": {...}
            }
        """

        logger.info("Running AI detection (heuristic-based)")

        # Use improved heuristic detection
        # This replaces the primitive MD5 hash approach
        result = detect_ai_basic(image_bytes)

        logger.info(f"AI detection complete: score={result['ai_score']:.2f}, verdict={result['primary_reason']}")

        return result
