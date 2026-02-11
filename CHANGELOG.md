# Changelog

All notable changes to TruthSnap Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-02-09

### Added
- **General Analysis Scenario**: New automatic scenario for users who send photos directly without scenario selection
  - Educational content about AI-generated images
  - Visual and technical red flag guides
  - Share functionality for analysis results
- Educational callback handlers (`general:ai_info`, `general:spotting_guide`)
- Improved user feedback messages during analysis queue

### Changed
- **BREAKING**: All users now receive full PRO-tier forensic analysis
  - Removed tier-based message formatting
  - Detailed digital footprint for all users
  - Complete red flags analysis for all users
- Enhanced analysis feedback messages with step-by-step progress indicators
- Updated scenario='general' for legacy flow (replaces scenario=None)

### Removed
- Free tier vs Pro tier message distinction
- "Upgrade to PRO" call-to-action messages

### Hidden (Temporarily)
- PDF report generation buttons (in testing phase)
  - Will be re-enabled after consumer endpoint stabilization
  - Buttons commented out but easily reversible

### Fixed
- Consumer endpoint PostgreSQL integration for TruthSnap Bot
- Gemini API model compatibility (gemini-1.5-flash)
- piexif error handling for images without EXIF data
- VerificationResult model now includes analysis_id field

## [0.2.0] - 2026-02-01

### Added
- Progressive UX with real-time status updates
- Scenario-based user flows (Adult Blackmail, Teenager SOS)
- PDF forensic report generation
- Counter-measures module for blackmail victims
- Parent communication helper for teenagers
- Watermark detection (SynthID, C2PA)
- PostgreSQL database integration

### Changed
- Migrated to scenario-based architecture
- Enhanced security with adversarial protection
- Improved rate limiting (5 msgs/min per user)

## [0.1.0] - 2026-01-13

### Added
- Initial bot release
- Basic photo analysis via FraudLens API
- Redis queue (RQ) for background processing
- MinIO S3 storage integration
- Basic subscription tiers (Free/Pro)
- Health check endpoints

---

## Migration Guide

### 0.2.x → 0.3.0

**For Users:**
- No action required
- All features automatically upgraded to PRO level
- PDF buttons temporarily hidden (will return)

**For Developers:**
1. Update environment variables (no changes required)
2. Restart bot container: `docker-compose restart bot`
3. Monitor logs for "scenario=general" entries
4. Test general analysis flow by sending photo directly to bot

**Database Changes:**
- No migrations required
- User tier field still exists but not used for message formatting

**API Changes:**
- Consumer endpoint now reads from PostgreSQL first, SQLite fallback
- VerificationResult includes analysis_id field
- Gemini detector uses gemini-1.5-flash model

---

## Support

For questions or issues:
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@truthsnap.ai
- Telegram: @TruthSnapSupport
