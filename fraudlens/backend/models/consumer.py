"""
Pydantic models for consumer API
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class ConsumerVerificationRequest(BaseModel):
    """Request model for consumer verification"""
    detail_level: str = Field(
        default="basic",
        description="Level of detail: 'basic' or 'detailed'"
    )


class WatermarkAnalysis(BaseModel):
    """Watermark detection result"""
    type: str = Field(description="Watermark type: synthid, c2pa, meta, none")
    confidence: float = Field(description="Detection confidence (0-1)")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class Finding(BaseModel):
    """Individual detection finding"""
    layer: str = Field(description="Detection layer name")
    status: str = Field(description="PASS or FAIL")
    score: float = Field(description="Layer-specific score")
    reason: str = Field(description="Human-readable reason")
    confidence: float = Field(description="Confidence in this finding")


class ConsumerVerificationResponse(BaseModel):
    """Response model for consumer verification"""
    verdict: str = Field(
        description="Final verdict: real, ai_generated, manipulated, inconclusive"
    )
    confidence: float = Field(
        description="Overall confidence score (0-1)"
    )
    watermark_detected: bool = Field(
        description="Whether AI watermark was found"
    )
    watermark_analysis: Optional[WatermarkAnalysis] = Field(
        default=None,
        description="Watermark details if detected"
    )
    processing_time_ms: int = Field(
        description="Analysis duration in milliseconds"
    )

    # Detailed fields (only if detail_level=detailed)
    findings: Optional[List[Finding]] = Field(
        default=None,
        description="Detailed findings from each detection layer"
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Image metadata analysis"
    )
    ai_signatures: Optional[Dict] = Field(
        default=None,
        description="AI generator signatures (Midjourney, DALL-E, etc.)"
    )
