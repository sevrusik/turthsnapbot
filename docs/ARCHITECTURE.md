# 🏗️ System Architecture - TruthSnap Bot

**Technical architecture and design decisions**

---

## 📐 Architecture Overview

TruthSnap uses a **microservices architecture** with async message queues for scalability and reliability.

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Users                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              TruthSnap Bot (aiogram 3.x)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Handlers  │  │Middlewares │  │   States   │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Redis  │  │ MinIO  │  │Postgres│
    │ Queue  │  │   S3   │  │   DB   │
    └───┬────┘  └────────┘  └────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│           RQ Workers (3 instances)                       │
│  ┌────────────────────────────────────────────────┐     │
│  │  analyze_photo_task()                          │     │
│  │  1. Download from S3                           │     │
│  │  2. Call FraudLens API                         │     │
│  │  3. Save result to DB                          │     │
│  │  4. Notify user                                │     │
│  │  5. Delete from S3                             │     │
│  └────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           FraudLens API (FastAPI)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │FFT Detector│  │  Metadata  │  │ Watermark  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend Services

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Bot** | Python 3.11 + aiogram 3.x | Telegram interface |
| **API** | Python 3.11 + FastAPI | Detection engine |
| **Workers** | Python + RQ | Background jobs |
| **Database** | PostgreSQL 16 | Persistent storage |
| **Queue** | Redis 7 | Job queue + cache |
| **Storage** | MinIO (S3-compatible) | Temporary photo storage |
| **Monitoring** | RQ Dashboard | Job monitoring |

### Libraries

**Bot**:
- `aiogram 3.x` - Telegram Bot framework
- `aiohttp` - Async HTTP client
- `redis` - Redis client

**API**:
- `FastAPI` - Web framework
- `NumPy` - Numerical computing
- `SciPy` - Scientific computing (FFT)
- `Pillow` - Image processing
- `uvicorn` - ASGI server

**Workers**:
- `rq` - Job queue
- `boto3` - S3 client

---

## 📊 Data Flow

### Scenario-Based Flow (New Architecture)

```
1. USER sends /start
   ↓
2. BOT shows scenario selection
   ├─ 👤 I'm being blackmailed (Adult)
   ├─ 🆘 I need help (Teenager)
   └─ 📚 Knowledge Base
   ↓
3. USER selects scenario → FSM state set
   ├─ AdultBlackmailStates.waiting_for_evidence
   └─ TeenagerSOSStates.psychological_stop (calming message)
   ↓
4. USER sends photo
   ↓
5. BOT receives photo in scenario context
   ├─ Validate image (size, format)
   ├─ Check rate limits (5 msg/min)
   ├─ Check daily quota (3/day free, unlimited pro)
   └─ Check adversarial patterns
   ↓
6. BOT uploads to S3 (MinIO)
   ├─ Generate unique key: {user_id}/{timestamp}.jpg
   ├─ Upload bytes
   └─ Get presigned URL (7-day expiry)
   ↓
7. BOT enqueues job to Redis WITH SCENARIO CONTEXT
   ├─ Priority: "high" (pro) or "default" (free)
   ├─ Job data: {user_id, photo_url, job_id, scenario: "adult_blackmail" | "teenager_sos"}
   └─ Send "In queue" message to user
   ↓
8. WORKER picks job from queue
   ├─ Download photo from S3
   ├─ Call FraudLens API
   ├─ Parse response
   └─ Save to database with scenario
   ↓
9. FRAUDLENS API analyzes photo
   ├─ FFT detection (31.5 img/s)
   ├─ Metadata analysis
   ├─ Watermark detection
   ├─ GPS extraction
   ├─ Calculate verdict + confidence
   └─ Return JSON result
   ↓
10. WORKER sends SCENARIO-SPECIFIC result
    ├─ Adult: Clinical tone + forensic evidence + SHA-256
    ├─ Teenager: Empathetic tone + simple language
    ├─ Generate PDF report
    └─ Show scenario-specific keyboard
   ↓
11. USER chooses next action:
    ├─ Adult: [📄 PDF] [🛡️ Counter-measures] [🔙 Menu]
    └─ Teenager: [📄 PDF] [🤝 Tell Parents] [🚫 Stop Spread] [📚 Education]
   ↓
12. SCENARIO-SPECIFIC ACTIONS:

    ADULT BLACKMAIL:
    ├─ Counter-measures
    │   ├─ Safe Response Generator (4 templates)
    │   ├─ StopNCII link
    │   ├─ FBI IC3 link
    │   └─ PDF download
    └─ Knowledge Base

    TEENAGER SOS:
    ├─ How to tell parents
    │   ├─ Conversation script
    │   └─ PDF to show parents
    ├─ Stop the Spread
    │   ├─ Take It Down (NCMEC)
    │   ├─ FBI Tips for Teens
    │   └─ CyberTipline
    └─ What is sextortion? (Education)
   ↓
13. WORKER cleanup
    ├─ Delete photo from S3 (privacy!)
    └─ Mark job as complete
```

**Total time**: 20-30 seconds (free), 10-15 seconds (pro)

---

## 🎯 Design Decisions

### Why Queue-Based Architecture?

**Benefits:**
- ✅ **Decouples** bot from heavy processing
- ✅ **Scalable** - add more workers easily
- ✅ **Reliable** - jobs persisted in Redis
- ✅ **Fair** - queue prevents resource starvation
- ✅ **Async** - bot stays responsive

**Alternatives considered:**
- ❌ Direct API calls - blocks bot, no retries
- ❌ Celery - heavier, more complex
- ✅ RQ - lightweight, simple, perfect for MVP

### Why S3 Storage?

**Benefits:**
- ✅ **Temporary** - presigned URLs expire
- ✅ **Scalable** - unlimited storage
- ✅ **Standard** - S3-compatible everywhere
- ✅ **Privacy** - auto-delete after analysis

**Alternatives considered:**
- ❌ Database blobs - inefficient, expensive
- ❌ Local filesystem - not scalable, lost on restart
- ✅ S3 - industry standard

### Why PostgreSQL?

**Benefits:**
- ✅ **ACID** - reliable transactions
- ✅ **JSON** - flexible schemas
- ✅ **Indexes** - fast queries
- ✅ **Mature** - battle-tested

**Alternatives considered:**
- ❌ MongoDB - less reliable for critical data
- ❌ SQLite - not scalable
- ✅ PostgreSQL - best for production

---

## 🔄 FSM State Management

TruthSnap uses **aiogram 3.x FSM (Finite State Machine)** for conversation flow.

### State Groups

```python
# bot/states.py

class ScenarioStates(StatesGroup):
    selecting_scenario = State()  # Initial scenario selection

class AdultBlackmailStates(StatesGroup):
    waiting_for_evidence = State()  # Waiting for photo upload
    reviewing_analysis = State()    # Analysis complete, showing results
    counter_measures = State()      # Counter-measures menu

class TeenagerSOSStates(StatesGroup):
    psychological_stop = State()    # Calming message shown
    waiting_for_photo = State()     # Waiting for photo upload
    ally_search = State()           # Parent communication helper
    emergency_protection = State()  # Take It Down, reporting
```

### State Transitions

```
/start
  ↓
ScenarioStates.selecting_scenario
  ↓
[User clicks "👤 I'm being blackmailed"]
  ↓
AdultBlackmailStates.waiting_for_evidence
  ↓
[User sends photo]
  ↓
AdultBlackmailStates.reviewing_analysis
  ↓
[User clicks "🛡️ Counter-measures"]
  ↓
AdultBlackmailStates.counter_measures


/start
  ↓
ScenarioStates.selecting_scenario
  ↓
[User clicks "🆘 I need help (Teenager)"]
  ↓
TeenagerSOSStates.psychological_stop (auto-shows calming message)
  ↓
TeenagerSOSStates.waiting_for_photo
  ↓
[User sends photo]
  ↓
TeenagerSOSStates.ally_search (shows support options)
```

### State Persistence

States are stored in **Redis** with TTL:
- Key: `fsm:{chat_id}:{user_id}:state`
- TTL: 1 hour (conversation timeout)
- Data: JSON with state name + context

**Example:**
```json
{
  "state": "AdultBlackmailStates:reviewing_analysis",
  "data": {
    "scenario": "adult_blackmail",
    "analysis_id": "ANL-20260118-abc123",
    "photo_s3_key": "123456789/1705584000.jpg"
  }
}
```

---

## 🗄️ Database Schema

### Users Table

```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    total_checks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_tier ON users(subscription_tier);
```

### Analyses Table

```sql
CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(50) UNIQUE,  -- ANL-YYYYMMDD-hash
    user_id BIGINT REFERENCES users(user_id),
    scenario VARCHAR(20),  -- adult_blackmail, teenager_sos, null (legacy)
    verdict VARCHAR(20),  -- real, ai_generated, manipulated, inconclusive
    confidence FLOAT,
    processing_time_ms INTEGER,
    detail_level VARCHAR(20),
    result_json JSONB,  -- Full detection results
    image_hash VARCHAR(64),  -- SHA-256 hash
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analyses_user ON analyses(user_id, created_at DESC);
CREATE INDEX idx_analyses_verdict ON analyses(verdict);
CREATE INDEX idx_analyses_scenario ON analyses(scenario);
CREATE INDEX idx_analyses_id ON analyses(analysis_id);
```

### Daily Usage Table

```sql
CREATE TABLE daily_usage (
    user_id BIGINT,
    date DATE,
    checks_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date)
);

CREATE INDEX idx_daily_usage_date ON daily_usage(date);
```

### Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    plan VARCHAR(20),  -- pro, pay_per_use
    status VARCHAR(20), -- active, canceled, expired
    stripe_subscription_id VARCHAR(255),
    started_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Payments Table

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    stripe_payment_id VARCHAR(255),
    status VARCHAR(20),  -- pending, completed, failed, refunded
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Security Events Table

```sql
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    event_type VARCHAR(50),  -- rate_limit, adversarial, suspicious
    severity VARCHAR(20),     -- low, medium, high
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_events_user ON security_events(user_id, created_at DESC);
```

---

## 🔐 Security Architecture

### 1. Rate Limiting

**Middleware**: `truthsnap-bot/app/bot/middlewares/rate_limit.py`

```python
class RateLimitMiddleware:
    def __init__(self):
        self.redis = Redis()
        self.limit = 5  # messages
        self.window = 60  # seconds

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        key = f"rate_limit:{user_id}"

        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)

        if count > self.limit:
            await event.answer("Too many requests. Wait 1 minute.")
            return

        return await handler(event, data)
```

### 2. Adversarial Protection

**Middleware**: `truthsnap-bot/app/bot/middlewares/adversarial.py`

Detects:
- Repeated uploads of same/similar images
- Rapid-fire uploads
- Pixel-shifted attacks
- Pattern-based attacks

```python
class AdversarialMiddleware:
    async def __call__(self, handler, event, data):
        if event.photo:
            # Calculate perceptual hash
            phash = calculate_phash(event.photo)

            # Check recent uploads
            recent = await get_recent_uploads(user_id, hours=1)

            if phash in recent:
                count = recent.count(phash)
                if count >= 5:
                    await flag_suspicious_activity(user_id)
                    await event.answer("⚠️ Suspicious activity detected")
                    return

        return await handler(event, data)
```

### 3. Input Validation

**Service**: `truthsnap-bot/app/services/image_validator.py`

```python
class ImageValidator:
    MAX_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_FORMATS = ["image/jpeg", "image/png", "image/webp"]

    def validate(self, file: UploadFile) -> bool:
        # Check size
        if file.size > self.MAX_SIZE:
            raise ValidationError("File too large")

        # Check format
        if file.content_type not in self.ALLOWED_FORMATS:
            raise ValidationError("Unsupported format")

        # Check if actually image
        try:
            Image.open(BytesIO(file.read()))
        except:
            raise ValidationError("Invalid image file")

        return True
```

---

## ⚡ Performance Optimizations

### 1. FFT Detector (177x Speedup)

**Before**: 5.6s per image
**After**: 0.032s per image

**Optimizations**:
1. Single FFT computation (was 4x)
2. Vectorized radial profile (`np.bincount`)
3. Removed `maximum_filter` (37ms → 4ms)
4. Precomputed geometric arrays

See [FFT_OPTIMIZATION.md](./FFT_OPTIMIZATION.md) for details.

### 2. Async Processing

**Bot & API use async/await throughout**:

```python
# Good - parallel
results = await asyncio.gather(
    storage.upload(photo),
    db.update_user(user_id),
    api.analyze(photo)
)

# Bad - sequential
await storage.upload(photo)
await db.update_user(user_id)
await api.analyze(photo)
```

### 3. Database Indexing

**Critical indexes**:
```sql
-- User lookups
CREATE INDEX idx_users_id ON users(user_id);

-- Analysis queries
CREATE INDEX idx_analyses_user_date ON analyses(user_id, created_at DESC);

-- Daily quota checks
CREATE INDEX idx_daily_usage ON daily_usage(user_id, date);
```

### 4. Caching Strategy

**Redis cache**:
- User data (TTL: 1 hour)
- Daily quota counts (TTL: 24 hours)
- Rate limit counters (TTL: 1 minute)

```python
@cache(ttl=3600)
async def get_user(user_id):
    return await db.query("SELECT * FROM users WHERE user_id = $1", user_id)
```

---

## 📈 Scalability

### Horizontal Scaling

**Workers** - Add more instances:
```yaml
# docker-compose.yml
truthsnap-worker:
  deploy:
    replicas: 10  # Scale from 3 to 10
```

**API** - Load balancer:
```
                    ┌─→ FraudLens API (instance 1)
Load Balancer (Nginx) ─→ FraudLens API (instance 2)
                    └─→ FraudLens API (instance 3)
```

**Database** - Read replicas:
```
Master (writes) ──→ Replica 1 (reads)
                ──→ Replica 2 (reads)
```

### Vertical Scaling

**Increase resources**:
- CPU: More cores for FFT parallelization
- RAM: Larger image processing
- Disk: More storage for logs

### Performance Metrics

| Load | Workers | API Instances | Throughput |
|------|---------|---------------|------------|
| **Low** (100 users/day) | 1 | 1 | 10 req/min |
| **Medium** (1000 users/day) | 3 | 2 | 100 req/min |
| **High** (10000 users/day) | 10 | 5 | 1000 req/min |
| **Enterprise** (100k users/day) | 50 | 20 | 10k req/min |

---

## 🚀 Deployment Architecture

### Development

```
Local Machine
├── Docker Compose
│   ├── Bot container
│   ├── API container
│   ├── Worker containers (3x)
│   ├── Redis container
│   ├── MinIO container
│   ├── PostgreSQL container
│   └── RQ Dashboard container
```

### Production (Railway/Fly.io/Render)

```
Cloud Platform
├── Bot Service (always-on)
├── API Service (autoscale 1-10)
├── Worker Service (autoscale 3-50)
├── Managed Redis
├── Managed PostgreSQL
└── AWS S3 / Cloudflare R2
```

### Multi-Region (Future)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   US-EAST   │     │   EU-WEST   │     │  ASIA-PAC   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ Bot + API   │     │ Bot + API   │     │ Bot + API   │
│ Workers     │     │ Workers     │     │ Workers     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    Global Database
                 (PostgreSQL + Replicas)
```

---

## 🔍 Monitoring & Observability

### Metrics

**Application metrics**:
- Request rate
- Error rate
- Response time (p50, p95, p99)
- Queue depth
- Worker utilization

**Business metrics**:
- Daily active users
- Analyses per day
- Subscription conversions
- Revenue (MRR, ARR)

### Logging

**Structured logging**:
```python
logger.info("photo_analyzed", extra={
    "user_id": user_id,
    "verdict": verdict,
    "confidence": confidence,
    "processing_time_ms": time_ms
})
```

**Log levels**:
- `DEBUG`: Development debugging
- `INFO`: Important events (analysis completed)
- `WARNING`: Degraded performance, rate limits
- `ERROR`: Failures, exceptions
- `CRITICAL`: System outages

### Alerting

**Alerts**:
- Error rate > 5% (5 min)
- API response time > 1s (p95)
- Queue depth > 1000 jobs
- Worker failure > 3 in 10 min
- Database connection loss

---

## 🔮 Future Architecture

### Phase 2: Real AI Models

```
FraudLens API
├── FFT Detector (existing)
├── Gemini Vision API
├── GPT-4V API
├── Claude Vision API
└── Ensemble Voter (combines all)
```

### Phase 3: Video Analysis

```
Video Input
├── Frame extraction (ffmpeg)
├── Batch analysis (parallel workers)
├── Temporal consistency check
└── Final verdict aggregation
```

### Phase 4: Edge Computing

```
CDN Edge Locations
├── Image preprocessing (resize, format)
├── Cache frequent results
├── Route to nearest API region
└── Reduce latency to <100ms
```

---

## 📚 References

- [FastAPI Architecture](https://fastapi.tiangolo.com/deployment/concepts/)
- [RQ Architecture](https://python-rq.org/docs/)
- [Microservices Patterns](https://microservices.io/patterns/)
- [System Design Primer](https://github.com/donnemartin/system-design-primer)

---

**Architecture designed for scale, reliability, and performance** 🚀
