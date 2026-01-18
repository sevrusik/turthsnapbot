"""
Application settings

Environment-based configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings
    """

    # App
    APP_NAME: str = "TruthSnap Bot"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    ADMIN_USER_IDS: str = ""  # Comma-separated list of admin Telegram IDs

    # FraudLens API
    FRAUDLENS_API_URL: str = "http://localhost:8000"
    FRAUDLENS_API_TIMEOUT: int = 60  # seconds

    # Database
    DATABASE_URL: str = "postgresql://truthsnap:password@localhost:5432/truthsnap"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 Storage
    S3_ENDPOINT: Optional[str] = None  # MinIO or AWS
    S3_BUCKET: str = "truthsnap-photos"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_dummy"
    STRIPE_WEBHOOK_SECRET: str = "whsec_dummy"
    STRIPE_PRICE_ID_PRO: str = "price_dummy"

    # Rate Limits
    MAX_PHOTO_SIZE_MB: int = 20
    RATE_LIMIT_PER_MINUTE: int = 5
    FREE_CHECKS_PER_DAY: int = 3

    # Adversarial Protection
    ADVERSARIAL_SIMILARITY_THRESHOLD: int = 5  # Hamming distance
    ADVERSARIAL_MAX_SIMILAR_UPLOADS: int = 10
    ADVERSARIAL_WINDOW_HOURS: int = 1

    # Security
    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin"""
        if not self.ADMIN_USER_IDS:
            return False
        admin_ids = [int(id.strip()) for id in self.ADMIN_USER_IDS.split(",") if id.strip()]
        return telegram_id in admin_ids


# Global settings instance
settings = Settings()
