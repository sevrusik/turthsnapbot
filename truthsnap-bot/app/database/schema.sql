-- TruthSnap Database Schema

-- Users table (already exists from user_repo.py)
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    daily_checks_remaining INTEGER DEFAULT 3,
    last_check_reset DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Analyses table (for PDF generation)
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(100) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    photo_hash VARCHAR(64) NOT NULL,
    photo_s3_key VARCHAR(500),
    preserve_exif BOOLEAN DEFAULT FALSE,
    verdict VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    watermark_detected BOOLEAN DEFAULT FALSE,
    watermark_type VARCHAR(100),
    full_result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_id (user_id),
    INDEX idx_analysis_id (analysis_id),
    INDEX idx_created_at (created_at)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_analysis_id ON analyses(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
