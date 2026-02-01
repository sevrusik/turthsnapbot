"""
Task Queue Service (RQ - Redis Queue)

Manages background job processing
"""

from redis import Redis
from rq import Queue
import logging
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class TaskQueue:
    """
    Redis Queue service for background tasks
    """

    def __init__(self):
        # Parse Redis URL
        redis_conn = Redis.from_url(settings.REDIS_URL)

        # Create queues with different priorities
        self.high_priority_queue = Queue('high', connection=redis_conn)
        self.default_queue = Queue('default', connection=redis_conn)
        self.low_priority_queue = Queue('low', connection=redis_conn)

    def enqueue_analysis(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
        photo_s3_key: str,
        tier: str,
        priority: str = "default",
        scenario: str = None,
        progress_message_id: int = None
    ) -> str:
        """
        Enqueue photo analysis task

        Args:
            user_id: Telegram user ID
            chat_id: Chat ID for response
            message_id: Message ID to reply to
            photo_s3_key: S3 key where photo is stored
            tier: User subscription tier (free/pro)
            priority: Queue priority (high/default/low)
            scenario: Scenario context (adult_blackmail/teenager_sos/None)
            progress_message_id: Message ID for progress updates (UX)

        Returns:
            job_id: Unique job ID
        """

        # Import task function
        from app.workers.tasks import analyze_photo_task

        # Select queue based on priority
        if priority == "high":
            queue = self.high_priority_queue
        elif priority == "low":
            queue = self.low_priority_queue
        else:
            queue = self.default_queue

        # Enqueue job
        job = queue.enqueue(
            'app.workers.tasks.analyze_photo_task',
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            photo_s3_key=photo_s3_key,
            tier=tier,
            scenario=scenario,
            progress_message_id=progress_message_id,
            job_timeout='5m',  # 5 minute timeout
            result_ttl=3600,  # Keep result for 1 hour
            failure_ttl=86400  # Keep failed jobs for 24 hours
        )

        logger.info(f"Enqueued analysis job: {job.id} | user={user_id} | priority={priority} | scenario={scenario} | progress_msg={progress_message_id}")

        return job.id

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """
        Get job status

        Args:
            job_id: Job ID

        Returns:
            {
                "status": "queued" | "started" | "finished" | "failed",
                "result": {...} or None
            }
        """
        from rq.job import Job

        try:
            redis_conn = Redis.from_url(settings.REDIS_URL)
            job = Job.fetch(job_id, connection=redis_conn)

            return {
                "status": job.get_status(),
                "result": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None
            }
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None
