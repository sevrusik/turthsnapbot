# TruthSnap Bot - Полная Архитектура и Система Обработки

## 📋 Общая Архитектура

TruthSnap Bot - это Telegram-бот для детектирования AI-сгенерированных изображений, предназначенный для помощи жертвам дипфейк-шантажа.

```
┌─────────────────────────────────────────────────────────────┐
│  USER FLOW: От Telegram до Результата                       │
└─────────────────────────────────────────────────────────────┘

1. User → Telegram Bot (aiogram 3.x)
          ↓
2. Scenario Selection (FSM States)
   - 👤 Adult Blackmail (Professional tone)
   - 🆘 Teenager SOS (Empathetic tone)
          ↓
3. Photo Upload (Photo or Document)
   - Photo: EXIF stripped by Telegram
   - Document: EXIF preserved
          ↓
4. Pre-validation (ImageValidator)
   - Format check (JPEG/PNG/MPO/HEIC)
   - Size check (< 20MB)
   - AI watermark detection (fast OCR)
   - Screenshot detection
          ↓
5. S3 Upload (MinIO)
   - Temporary storage
   - S3 key: temp/{user_id}/{file_id}.jpg
          ↓
6. Redis Queue (RQ)
   - Priority: high (pro) / default (free)
   - Job metadata: user_id, chat_id, s3_key, tier, scenario
          ↓
7. RQ Worker (Background Processing)
   - Download from S3
   - Call FraudLens API
   - Save to PostgreSQL
          ↓
8. FraudLens API (External Service)
   - Multi-layer detection
   - Returns verdict + confidence + fraud_score
          ↓
9. Notification Service (BotNotifier)
   - Format result (Free vs Pro)
   - Scenario-aware keyboard
   - Send to Telegram
          ↓
10. User Receives Result
    - Basic: Verdict + Confidence
    - Pro: Detailed EXIF + GPS + Forensics
```

---

## 🏗️ Компоненты Системы

### **1. Telegram Bot** (`truthsnap-bot/app/bot/`)

**Технологии:**
- **aiogram 3.x** - async Telegram Bot framework
- **FSM (Finite State Machine)** - управление состояниями пользователя
- **Inline Keyboards** - интерактивные кнопки

**Обработчики (Handlers):**

| Handler | Файл | Назначение |
|---------|------|-----------|
| `/start` | `handlers/start.py` | Приветствие + выбор сценария |
| Scenarios | `handlers/scenarios.py` | Adult Blackmail / Teenager SOS |
| Photo Upload | `handlers/scenarios.py` | Загрузка фото/документа |
| Counter-measures | `handlers/counter_measures.py` | Контр-меры для взрослых |
| Parent Support | `handlers/parent_support.py` | Помощь подросткам |
| Callbacks | `handlers/callbacks.py` | Обработка callback_query |

**FSM States:**

```python
# Scenario Selection
ScenarioStates.selecting_scenario

# Adult Blackmail Flow
AdultBlackmailStates.waiting_for_evidence
AdultBlackmailStates.analyzing
AdultBlackmailStates.result_shown

# Teenager SOS Flow
TeenagerSOSStates.psychological_stop
TeenagerSOSStates.waiting_for_photo
TeenagerSOSStates.analyzing
TeenagerSOSStates.result_shown
TeenagerSOSStates.tell_parent
```

---

### **2. Background Workers** (`truthsnap-bot/app/workers/`)

**RQ (Redis Queue)** - распределенная система очередей для фоновой обработки.

**Задачи (Tasks):**

```python
def analyze_photo_task(
    user_id: int,
    chat_id: int,
    message_id: int,
    photo_s3_key: str,
    tier: str,  # "photo", "document", "free", "pro"
    scenario: str  # "adult_blackmail", "teenager_sos", None
)
```

**Этапы обработки:**

```
STAGE 1: Job received
  - Worker picks up task from Redis

STAGE 2: Download from S3 (100-300ms)
  - MinIO download
  - Get photo bytes

STAGE 3: FraudLens API call (20-30s)
  - detail_level: "basic" (photo) or "detailed" (document)
  - preserve_exif: True (document) or False (photo)
  - Returns: verdict, confidence, fraud_score, details

STAGE 4: Save to PostgreSQL (50-100ms)
  - Create analysis record
  - SHA-256 hash
  - Full result JSON
  - Get user subscription tier

STAGE 5: Send to Telegram (200-500ms)
  - Format message (Free vs Pro)
  - Scenario-aware keyboard
  - Send notification

STAGE 6: Keep photo in S3
  - For PDF generation (on-demand)
  - Auto-cleanup after 24h (lifecycle policy)
```

**Worker Configuration:**

```yaml
# docker-compose.yml
truthsnap-worker:
  replicas: 3  # 3 parallel workers
  command: rq worker high default low --url redis://redis:6379/0

  Queues:
    - high: Pro users (faster processing)
    - default: Free users
    - low: Batch jobs
```

---

### **3. Services** (`truthsnap-bot/app/services/`)

#### **3.1. FraudLens Client** (`fraudlens_client.py`)

```python
class FraudLensClient:
    async def verify_photo(
        image_bytes: bytes,
        detail_level: str = "basic",  # "basic" or "detailed"
        preserve_exif: bool = False   # True for documents
    ) -> Dict
```

**Endpoints:**

| Endpoint | Method | Назначение |
|----------|--------|-----------|
| `/api/v1/consumer/verify` | POST | Анализ фото |
| `/api/v1/consumer/report/pdf` | POST | Генерация PDF |
| `/api/v1/health` | GET | Health check |

**Response Format:**

```json
{
    "verdict": "real" | "ai_generated" | "manipulated" | "inconclusive",
    "confidence": 0.95,
    "verdict_reason": "AI detection model score: 0.95",
    "watermark_detected": false,
    "watermark_analysis": null,
    "processing_time_ms": 2340,
    "details": {
        "detection_layer": "ai_model",
        "fraud_score": 87,
        "ai_detection_score": 0.85,
        "intrinsic_score": 50,
        "exif_fraud_score": 0,
        "camera_model": "iPhone 13 Pro",
        "device_info": {...},
        "red_flags": []
    }
}
```

#### **3.2. Storage Service** (`storage.py`)

```python
class S3Storage:
    async def upload(data: bytes, s3_key: str)
    async def download(s3_key: str) -> bytes
    async def delete(s3_key: str)
    async def generate_presigned_url(s3_key: str, expires: int) -> str
```

**S3 Structure:**

```
truthsnap-photos/
├── temp/{user_id}/{file_id}.jpg     # Временные фото (24h TTL)
└── reports/{analysis_id}.pdf         # PDF отчеты (7 days TTL)
```

#### **3.3. Queue Service** (`queue.py`)

```python
class TaskQueue:
    def enqueue_analysis(
        user_id: int,
        chat_id: int,
        message_id: int,
        photo_s3_key: str,
        tier: str,
        priority: str = "default"  # "high" or "default"
    ) -> str  # job_id
```

**Priority Mapping:**

```python
if user['subscription_tier'] == 'pro':
    priority = "high"    # Queue: high (faster)
else:
    priority = "default" # Queue: default
```

#### **3.4. Notification Service** (`notifications.py`)

**Форматирует результаты анализа для пользователя.**

```python
class BotNotifier:
    async def send_analysis_result(
        chat_id: int,
        message_id: int,
        result: Dict,
        tier: str,  # "free" or "pro"
        analysis_id: str,
        scenario: str  # "adult_blackmail", "teenager_sos", None
    )
```

**Message Formatting:**

##### **Free Tier Message:**

```
🟢 Photo Appears Real

Confidence: 92.5%

⏱ Analysis time: 2.3s

💡 Upgrade to Pro for:
• Full forensic report
• Camera metadata (Make, Model, GPS)
• PDF export for legal evidence
• Priority processing (10-15s)

[🔬 Generate PDF Report (Pro)]
[⬅️ Back to Menu]
```

##### **Pro Tier Message:**

```
🟢 Photo Appears Real

━━━━━━━━━━━━━━━━━━━━━━
📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━

🤖 AI Detection: 5/100 (Very Low)
🔬 Manipulation Score: 12/100 (Clean)
📸 EXIF Integrity: 100% Valid

━━━━━━━━━━━━━━━━━━━━━━
📷 Camera Evidence
━━━━━━━━━━━━━━━━━━━━━━

📱 Device: Apple iPhone 13 Pro
📅 Captured: 16 Dec 2025, 07:42
💾 Software: iOS 15.2
📍 Location: San Francisco, USA

━━━━━━━━━━━━━━━━━━━━━━
🔐 Forensic Hash
━━━━━━━━━━━━━━━━━━━━━━

SHA-256: a3f5b8c...
Report ID: R-2026-01-1234

⏱ Analysis time: 2.3s

[📄 Download PDF Report]
[🛡️ Counter-Measures]
[⬅️ Back to Menu]
```

**Scenario-Aware Keyboards:**

| Scenario | Buttons |
|----------|---------|
| Adult Blackmail | `[Generate PDF] [Counter-Measures] [Back]` |
| Teenager SOS | `[Generate PDF] [Tell Parents] [Emergency Help] [Back]` |
| None (Legacy) | `[Generate PDF] [Back]` |

---

### **4. Database** (`truthsnap-bot/app/database/`)

**PostgreSQL Schema:**

```sql
-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    daily_checks_remaining INT DEFAULT 3,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analyses table
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(telegram_id),
    photo_hash VARCHAR(64) NOT NULL,  -- SHA-256
    verdict VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    full_result JSONB NOT NULL,
    photo_s3_key VARCHAR(255),
    preserve_exif BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table (planned)
CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id),
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(50),
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Repositories:**

```python
# user_repo.py
class UserRepository:
    async def get_user(telegram_id: int) -> Dict
    async def create_user(telegram_id: int, username: str) -> Dict
    async def can_user_analyze(telegram_id: int) -> Tuple[bool, str]
    async def decrement_daily_checks(telegram_id: int)
    async def reset_daily_checks_if_needed(telegram_id: int)

# analysis_repo.py
class AnalysisRepository:
    async def create_analysis(...) -> str  # returns analysis_id
    async def get_analysis(analysis_id: str) -> Dict
    async def get_user_analyses(telegram_id: int, limit: int) -> List[Dict]
```

---

### **5. Middlewares** (`truthsnap-bot/app/bot/middlewares/`)

#### **5.1. Rate Limiting** (`rate_limit.py`)

```python
class RateLimitMiddleware:
    """
    Защита от спама

    Limits:
    - 5 messages per minute per user
    - 30 messages per hour per user

    Uses Redis for distributed rate limiting
    """
```

#### **5.2. Adversarial Protection** (`adversarial.py`)

```python
class AdversarialMiddleware:
    """
    Защита от adversarial attacks

    Detects:
    - Pixel-shifted photos (same pHash with slight modifications)
    - Suspicious upload patterns
    - Repeated analysis attempts
    """
```

#### **5.3. Logging Middleware** (`logging.py`)

```python
class LoggingMiddleware:
    """
    Логирование всех событий

    Logs:
    - User actions
    - Commands
    - Errors
    - Processing time
    """
```

---

## 🎭 Сценарии Использования

### **Сценарий 1: Adult Blackmail (👤 I'm being blackmailed)**

**Целевая аудитория:** Взрослые люди, которых шантажируют поддельными интимными фото.

**Тон:** Холодный, клинический, профессиональный, юридически-ориентированный.

**Flow:**

```
Step 1: Evidence Analysis
  ↓
User uploads photo (as photo or document)
  ↓
Bot: "🔍 Analyzing evidence..."
  ↓
Result:
  - Verdict: AI-generated / Real / Manipulated
  - Confidence: 95%
  - SHA-256 Hash (legal proof)
  - Report ID (for authorities)
  ↓
Step 2: PDF Report Generation
  ↓
Bot: [📄 Generate Legal Report]
  ↓
Worker generates forensic PDF with:
  - Technical analysis
  - EXIF metadata
  - Hash verification
  - Legal disclaimer
  ↓
Step 3: Counter-Measures
  ↓
Bot: [🛡️ Counter-Measures]
  ↓
Options:
  - ✍️ Safe Response Generator (AI-crafted responses)
  - 🚫 Block Blackmailer (how-to guide)
  - 📚 Legal Resources
  - 🌐 StopNCII (hash-based removal)
  - 🕵️ Report to FBI IC3
```

**Example Message (AI-generated verdict):**

```
🤖 AI-Generated Image Detected

━━━━━━━━━━━━━━━━━━━━━━
📊 Evidence Summary
━━━━━━━━━━━━━━━━━━━━━━

🤖 AI Detection: 87/100 (High)
🔬 Manipulation Score: 72/100 (Suspicious)
📸 EXIF Integrity: N/A (stripped)

━━━━━━━━━━━━━━━━━━━━━━
⚖️ Legal Evidence
━━━━━━━━━━━━━━━━━━━━━━

SHA-256: a3f5b8c2d4e6f...
Report ID: R-2026-01-1234
Timestamp: 31 Jan 2026, 22:45 UTC

⚠️ This photo is AI-generated.
The blackmailer is using fake evidence.

[📄 Generate Legal Report]
[🛡️ Counter-Measures]
[⬅️ Back to Menu]
```

---

### **Сценарий 2: Teenager SOS (🆘 I need help)**

**Целевая аудитория:** Подростки, которых шантажируют (sextortion).

**Тон:** Эмпатичный, поддерживающий, образовательный.

**Flow:**

```
Step 1: Psychological Stop
  ↓
Bot: "Breathe. You're safe. This is not your fault."
  ↓
Step 2: Photo Analysis (Empathetic)
  ↓
User uploads photo
  ↓
Bot: "Let's look at the evidence together..."
  ↓
Result (empathetic language):
  - "This photo is likely fake" (not "AI-generated")
  - "You have legal protection"
  - "Many people face this - you're not alone"
  ↓
Step 3: Tell Parents
  ↓
Bot: [👨‍👩‍👧 How to Tell Parents]
  ↓
Options:
  - 📝 Conversation Script
  - ❓ FAQ (What will they say?)
  - 🎯 Best Time to Tell
  - 💪 They Will Support You
  ↓
Step 4: Emergency Protection
  ↓
Bot: [🆘 Stop the Spread]
  ↓
Options:
  - 🛑 Take It Down (NCMEC anonymous removal)
  - 📞 CyberTipline (report anonymously)
  - 🕵️ FBI Tips for Teens
  - 📚 Educational Resources
```

**Example Message (AI-generated verdict):**

```
🛡️ You're Safe - This Photo is Fake

━━━━━━━━━━━━━━━━━━━━━━
💡 What This Means
━━━━━━━━━━━━━━━━━━━━━━

✅ This photo was created by AI software
✅ It's NOT a real photo of you
✅ This is a COMMON blackmail tactic
✅ You have legal protection

━━━━━━━━━━━━━━━━━━━━━━
🤝 Next Steps
━━━━━━━━━━━━━━━━━━━━━━

1️⃣ Do NOT pay the blackmailer
2️⃣ Screenshot this analysis
3️⃣ Tell a trusted adult
4️⃣ Report to authorities

This happens to MANY people. You did nothing wrong.

[👨‍👩‍👧 How to Tell Parents]
[🆘 Stop the Spread]
[⬅️ Back to Menu]
```

---

## 📊 Тарифные Планы и Лимиты

### **Free Tier**

```python
DAILY_CHECKS: 3
RESET_TIME: 00:00 UTC

Features:
  - Basic verdict (Real / AI / Manipulated)
  - Confidence score
  - SHA-256 hash
  - Report ID
  - Scenario-based support

Limitations:
  - No detailed EXIF
  - No GPS location
  - No PDF download
  - Slower processing (default queue)
```

**Free Tier Message Format:**

```
🟢 Photo Appears Real

Confidence: 92.5%

⏱ Analysis time: 2.3s

━━━━━━━━━━━━━━━━━━━━━━
📊 Checks Remaining Today
━━━━━━━━━━━━━━━━━━━━━━

✅ 2 / 3 checks left
🔄 Resets in 4h 15m

💡 Upgrade to Pro for:
• Unlimited checks
• Full forensic report
• Camera metadata
• GPS location
• PDF export
• Priority processing (10-15s)

[⭐ Upgrade to Pro ($9.99/mo)]
[⬅️ Back to Menu]
```

---

### **Pro Tier ($9.99/month)**

```python
DAILY_CHECKS: Unlimited
PRIORITY_QUEUE: true

Features:
  - Everything in Free
  + Detailed EXIF metadata
  + Camera Make/Model
  + GPS location (reverse geocoded)
  + PDF forensic report
  + Priority processing (high queue)
  + Analysis history

Processing Time:
  - Free: 20-30 seconds (default queue)
  - Pro: 10-15 seconds (high queue)
```

**Pro Tier Message Format:**

```
🟢 Photo Appears Real

━━━━━━━━━━━━━━━━━━━━━━
📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━

🤖 AI Detection: 5/100 (Very Low)
🔬 Manipulation Score: 12/100 (Clean)
📸 EXIF Integrity: 100% Valid

━━━━━━━━━━━━━━━━━━━━━━
📷 Camera Evidence
━━━━━━━━━━━━━━━━━━━━━━

📱 Device: Apple iPhone 13 Pro
📅 Captured: 16 Dec 2025, 07:42
💾 Software: iOS 15.2
📍 Location: San Francisco, USA

━━━━━━━━━━━━━━━━━━━━━━
🔐 Forensic Hash
━━━━━━━━━━━━━━━━━━━━━━

SHA-256: a3f5b8c2d4e6f1a8...
Report ID: R-2026-01-1234

⏱ Analysis time: 1.2s

[📄 Download PDF Report]
[🛡️ Counter-Measures]
[📊 Analysis History]
[⬅️ Back to Menu]
```

---

## 🔒 Безопасность

### **1. Rate Limiting**

```python
# Redis keys
rate_limit:user:{telegram_id}:minute  # 5 messages/minute
rate_limit:user:{telegram_id}:hour    # 30 messages/hour

# Response
if rate_limited:
    await message.answer(
        "⏳ <b>Rate limit exceeded</b>\n\n"
        "Please wait {seconds} seconds before sending another message.",
        parse_mode="HTML"
    )
```

---

### **2. Adversarial Protection**

**pHash (Perceptual Hash) Detection:**

```python
# Detect pixel-shifted photos
validation_report = await validator.validate(image_bytes)

if validation_report.phash:
    # Check if similar photo analyzed recently
    recent_analysis = await db.find_by_phash(
        phash=validation_report.phash,
        user_id=user_id,
        within_hours=24
    )

    if recent_analysis:
        await message.answer(
            "⚠️ <b>Duplicate Photo Detected</b>\n\n"
            "You uploaded a very similar photo recently.\n"
            "Analysis ID: {recent_analysis['id']}\n\n"
            "This check was NOT deducted.",
            parse_mode="HTML"
        )
        return  # Don't process
```

---

### **3. Privacy & Data Retention**

```python
# S3 Lifecycle Policies
temp/{user_id}/*      # Delete after 24 hours
reports/{id}.pdf      # Delete after 7 days

# Database
analyses table        # Keep forever (for history)
  - photo_s3_key removed after S3 cleanup
  - only hash + verdict remain
```

---

## 📈 Performance & Monitoring

### **Processing Time Breakdown:**

```
User sends photo
  ↓
Telegram → Bot (100-200ms)
  ↓
Download from Telegram (200-500ms)
  ↓
Validation (50-100ms)
  ↓
S3 Upload (100-300ms)
  ↓
Redis Enqueue (10-20ms)
  ↓
Bot Response "Analyzing..." (100-200ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL USER-FACING LATENCY: ~1 second
━━━━━━━━━━━━━━━━━━━━━━━━━━

[Background Worker picks up job]
  ↓
S3 Download (100-300ms)
  ↓
FraudLens API Call (20-30s FREE, 10-15s PRO)
  ↓
PostgreSQL Save (50-100ms)
  ↓
Telegram Notification (200-500ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL BACKGROUND TIME: 21-31 seconds
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Monitoring Dashboards:**

#### **1. RQ Dashboard** (http://localhost:9181)

```
Queues:
  - high:    12 jobs (Pro users)
  - default: 45 jobs (Free users)
  - low:     3 jobs (Batch)

Workers:
  - worker-1: BUSY (processing job abc123)
  - worker-2: BUSY (processing job def456)
  - worker-3: IDLE

Failed Jobs:
  - job xyz789: TimeoutError (retry 2/3)
```

#### **2. MinIO Console** (http://localhost:9001)

```
Buckets:
  truthsnap-photos/
    ├── temp/         (2.3 GB, 1,234 objects)
    └── reports/      (450 MB, 89 objects)

Storage Usage: 2.75 GB / 100 GB
```

#### **3. Application Logs**

```bash
# Bot logs
docker-compose logs -f truthsnap-bot

# Worker logs
docker-compose logs -f truthsnap-worker

# API logs
docker-compose logs -f fraudlens-api
```

---

## 🔄 Error Handling

### **1. FraudLens API Errors**

```python
try:
    result = await fraudlens.verify_photo(photo_bytes)
except AnalysisTimeoutError:
    await bot.send_message(
        chat_id,
        "⏳ Analysis took too long. Please try again.\n"
        "Your check was NOT deducted."
    )
except AuthenticationError:
    await bot.send_message(
        chat_id,
        "❌ API authentication failed. Please contact support."
    )
except RateLimitError:
    await bot.send_message(
        chat_id,
        "⏳ API rate limit exceeded. Please try again in 1 minute."
    )
except AnalysisError as e:
    await bot.send_message(
        chat_id,
        f"❌ Analysis failed: {str(e)}\n"
        "Please try again or contact support."
    )
```

---

### **2. S3 Errors**

```python
try:
    await s3.upload(photo_bytes, s3_key)
except Exception as e:
    logger.error(f"S3 upload failed: {e}")
    await message.answer("❌ Upload failed. Please try again.")
    return
```

---

### **3. Redis Queue Errors**

```python
try:
    job_id = queue.enqueue_analysis(...)
except Exception as e:
    logger.error(f"Queue enqueue failed: {e}")
    await message.answer(
        "❌ Failed to queue analysis. Please try again.\n"
        "Your check was NOT deducted."
    )
    # Refund user check
    await user_repo.increment_daily_checks(user_id)
    return
```

---

## 📦 Response Examples

### **Example 1: Real Photo (Pro Tier, Adult Blackmail)**

```
🟢 Photo Appears Real

━━━━━━━━━━━━━━━━━━━━━━
📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━

🤖 AI Detection: 5/100 (Very Low)
🔬 Manipulation Score: 12/100 (Clean)
📸 EXIF Integrity: 100% Valid

━━━━━━━━━━━━━━━━━━━━━━
📷 Camera Evidence
━━━━━━━━━━━━━━━━━━━━━━

📱 Device: Apple iPhone 13 Pro
📅 Captured: 16 Dec 2025, 07:42
💾 Software: iOS 15.2
📍 Location: San Francisco, USA

━━━━━━━━━━━━━━━━━━━━━━
🔐 Forensic Hash
━━━━━━━━━━━━━━━━━━━━━━

SHA-256: a3f5b8c2d4e6f1a8b9c0d1e2f3g4h5i6
Report ID: R-2026-01-1234

⏱ Analysis time: 1.2s

[📄 Generate Legal Report]
[🛡️ Counter-Measures]
[⬅️ Back to Menu]
```

---

### **Example 2: AI-Generated (Free Tier, Teenager SOS)**

```
🛡️ You're Safe - This Photo is Fake

Confidence: 95.0%

⏱ Analysis time: 2.3s

━━━━━━━━━━━━━━━━━━━━━━
💡 What This Means
━━━━━━━━━━━━━━━━━━━━━━

✅ This photo was created by AI software
✅ It's NOT a real photo of you
✅ This is a COMMON blackmail tactic
✅ You have legal protection

━━━━━━━━━━━━━━━━━━━━━━
🤝 Next Steps
━━━━━━━━━━━━━━━━━━━━━━

1️⃣ Do NOT pay the blackmailer
2️⃣ Screenshot this analysis
3️⃣ Tell a trusted adult
4️⃣ Report to authorities

This happens to MANY people. You did nothing wrong.

━━━━━━━━━━━━━━━━━━━━━━
📊 Checks Remaining Today
━━━━━━━━━━━━━━━━━━━━━━

✅ 2 / 3 checks left
🔄 Resets in 4h 15m

[👨‍👩‍👧 How to Tell Parents]
[🆘 Stop the Spread]
[⬅️ Back to Menu]
```

---

### **Example 3: Manipulated Photo (Pro Tier, Adult Blackmail)**

```
⚠️ Photo May Be Manipulated

━━━━━━━━━━━━━━━━━━━━━━
📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━

🤖 AI Detection: 42/100 (Medium)
🔬 Manipulation Score: 58/100 (Suspicious)
📸 EXIF Integrity: 65% Questionable

━━━━━━━━━━━━━━━━━━━━━━
⚠️ Red Flags Detected
━━━━━━━━━━━━━━━━━━━━━━

⚠️ Inconsistent EXIF timestamps
⚠️ Suspicious noise patterns
⚠️ Possible pixel-level editing

━━━━━━━━━━━━━━━━━━━━━━
📷 Camera Metadata
━━━━━━━━━━━━━━━━━━━━━━

📱 Device: Samsung Galaxy S21
📅 Captured: 15 Dec 2025, 18:30
💾 Software: Adobe Photoshop 2024
📍 Location: N/A (stripped)

━━━━━━━━━━━━━━━━━━━━━━
🔐 Forensic Hash
━━━━━━━━━━━━━━━━━━━━━━

SHA-256: b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9
Report ID: R-2026-01-1235

⏱ Analysis time: 1.8s

💡 This photo shows signs of manipulation.
Consider this evidence when responding to the blackmailer.

[📄 Generate Legal Report]
[🛡️ Counter-Measures]
[⬅️ Back to Menu]
```

---

## 🚀 Deployment

### **Production Architecture (Railway/Fly.io)**

```
┌─────────────────────────────────────────┐
│  PRODUCTION SERVICES                     │
└─────────────────────────────────────────┘

1. FraudLens API (Web Service)
   - Port: 8000
   - Replicas: 2
   - Resources: 1GB RAM, 1 CPU

2. TruthSnap Bot (Worker Service)
   - Replicas: 1
   - Resources: 512MB RAM, 0.5 CPU
   - Command: python -m app.bot.main

3. RQ Workers (Worker Service)
   - Replicas: 3
   - Resources: 1GB RAM, 1 CPU
   - Command: rq worker high default low

4. Redis (Managed Service)
   - Plan: Upstash / Railway Redis
   - Resources: 256MB

5. PostgreSQL (Managed Service)
   - Plan: Railway Postgres / Supabase
   - Resources: 1GB

6. S3 Storage (Managed Service)
   - AWS S3 / MinIO Cloud
   - Lifecycle: 24h temp, 7d reports
```

---

## 📊 Metrics & KPIs

### **Target Metrics (Month 1)**

```
Users:           1,000
Premium Users:   50 (5% conversion)
MRR:             $500 ($9.99 × 50)

Analyses:        5,000
Accuracy:        95%+
Uptime:          99%+

Avg Response:    <25s
Bot Latency:     <1s
API Latency:     <3s
```

---

## 📚 References

- **aiogram Documentation**: https://docs.aiogram.dev/
- **Redis Queue (RQ)**: https://python-rq.org/
- **FraudLens API**: http://localhost:8000/docs
- **MinIO S3**: https://min.io/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

**Generated by**: TruthSnap Team
**Last Updated**: 2026-01-31
**Version**: 2.0
