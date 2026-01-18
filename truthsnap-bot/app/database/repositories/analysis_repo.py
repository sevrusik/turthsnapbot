"""
Analysis Repository

Database operations for analyses
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from database.db import db

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """
    Analysis data access layer

    Uses PostgreSQL for shared storage between workers and bot
    """

    async def create_analysis(
        self,
        user_id: int,
        photo_hash: str,
        verdict: str,
        confidence: float,
        full_result: Dict,
        photo_s3_key: Optional[str] = None,
        preserve_exif: bool = False
    ) -> str:
        """
        Create new analysis record

        Args:
            user_id: Telegram user ID
            photo_hash: SHA-256 hash of photo
            verdict: Analysis verdict
            confidence: Confidence score
            full_result: Full analysis result
            photo_s3_key: S3 key for photo (for PDF generation)
            preserve_exif: Whether EXIF was preserved

        Returns:
            analysis_id: Unique analysis ID
        """

        # Generate analysis ID using database sequence
        import uuid
        analysis_id = f"ANL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        watermark_detected = full_result.get('watermark_detected', False)
        watermark_type = (full_result.get('watermark_analysis') or {}).get('type')

        # Insert into PostgreSQL
        query = """
            INSERT INTO analyses (
                analysis_id, user_id, photo_hash, photo_s3_key, preserve_exif,
                verdict, confidence, watermark_detected, watermark_type,
                full_result, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING analysis_id
        """

        result = await db.fetchrow(
            query,
            analysis_id,
            user_id,
            photo_hash,
            photo_s3_key,
            preserve_exif,
            verdict,
            confidence,
            watermark_detected,
            watermark_type,
            json.dumps(full_result),
            datetime.now()
        )

        logger.info(
            f"Created analysis: {analysis_id} | "
            f"user={user_id} | verdict={verdict} | confidence={confidence:.2f}"
        )

        return analysis_id

    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        Get analysis by ID

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis dict or None
        """
        query = """
            SELECT analysis_id, user_id, photo_hash, photo_s3_key, preserve_exif,
                   verdict, confidence, watermark_detected, watermark_type,
                   full_result, created_at
            FROM analyses
            WHERE analysis_id = $1
        """

        row = await db.fetchrow(query, analysis_id)

        if not row:
            return None

        return {
            'analysis_id': row['analysis_id'],
            'user_id': row['user_id'],
            'photo_hash': row['photo_hash'],
            'photo_s3_key': row['photo_s3_key'],
            'preserve_exif': row['preserve_exif'],
            'verdict': row['verdict'],
            'confidence': row['confidence'],
            'watermark_detected': row['watermark_detected'],
            'watermark_type': row['watermark_type'],
            'full_result': json.loads(row['full_result']) if row['full_result'] else {},
            'created_at': row['created_at']
        }

    async def get_user_analyses(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get analyses for user

        Args:
            user_id: Telegram user ID
            limit: Max number of results

        Returns:
            List of analysis dicts
        """

        user_analyses = [
            a for a in self._analyses.values()
            if a['user_id'] == user_id
        ]

        # Sort by created_at descending
        user_analyses.sort(key=lambda x: x['created_at'], reverse=True)

        return user_analyses[:limit]

    async def get_stats(self) -> Dict:
        """
        Get overall statistics

        Returns:
            {
                "total_analyses": int,
                "verdicts": {...},
                "avg_confidence": float
            }
        """

        total = len(self._analyses)

        if total == 0:
            return {
                "total_analyses": 0,
                "verdicts": {},
                "avg_confidence": 0.0
            }

        # Count verdicts
        verdicts = {}
        total_confidence = 0.0

        for analysis in self._analyses.values():
            verdict = analysis['verdict']
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            total_confidence += analysis['confidence']

        avg_confidence = total_confidence / total

        return {
            "total_analyses": total,
            "verdicts": verdicts,
            "avg_confidence": avg_confidence
        }
