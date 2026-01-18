# 🎯 TruthSnap Bot

**AI-Generated Image Detection for Telegram**

Instantly verify if a photo is real or AI-generated. Designed to help victims of deepfake blackmail and revenge porn.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 1. Clone & Configure

```bash
# Clone repository
git clone <your-repo>
cd TruthSnapBot

# Copy environment file
cp .env.example .env

# Edit .env and add your Telegram bot token
nano .env
```

### 2. Start Services

```bash
# Start all services (API + Bot + Workers + Redis + MinIO)
docker-compose up -d

# View logs
docker-compose logs -f truthsnap-bot

# Check status
docker-compose ps
```

### 3. Test Bot

1. Open Telegram
2. Find your bot (username from BotFather)
3. Send `/start`
4. Choose your scenario:
   - 👤 **I'm being blackmailed** (Adult/General)
   - 🆘 **I need help (Teenager)**
5. Upload a photo
6. Wait 20-30 seconds for analysis

---

## 🏗️ Architecture

```
User chooses scenario → Telegram Bot (aiogram 3.x)
    ↓
Scenario-aware FSM states
    ↓
Redis Queue (RQ) with scenario context
    ↓
FraudLens API (FastAPI)
    ↓
Scenario-specific response + PDF report
    ↓
S3 Storage (MinIO)
```

### Components

- **FraudLens API** (`:8000`) - AI detection engine
- **TruthSnap Bot** - Telegram bot interface
- **RQ Workers** (x3) - Background job processors
- **Redis** (`:6379`) - Queue & cache
- **MinIO** (`:9000`) - S3-compatible storage
- **RQ Dashboard** (`:9181`) - Job monitoring

---

## 📁 Project Structure

```
TruthSnapBot/
├── fraudlens/                    # Detection API
│   └── backend/
│       ├── api/routes/
│       │   └── consumer.py       # Consumer endpoint
│       ├── integrations/
│       │   ├── watermark_detector.py
│       │   └── metadata.py
│       ├── core/
│       │   └── fraud_detector.py
│       └── models/
│           └── consumer.py
│
├── truthsnap-bot/                # Telegram bot
│   └── app/
│       ├── bot/
│       │   ├── handlers/         # Message handlers
│       │   │   ├── scenarios.py  # Scenario flows
│       │   │   ├── counter_measures.py  # Adult counter-measures
│       │   │   ├── parent_support.py    # Teenager support
│       │   │   └── photo.py      # Photo analysis
│       │   ├── keyboards/        # Inline keyboards
│       │   │   └── scenarios.py  # Scenario keyboards
│       │   ├── middlewares/      # Security middlewares
│       │   ├── states.py         # FSM states
│       │   └── main.py           # Bot entry point
│       ├── workers/
│       │   └── tasks.py          # Background tasks
│       ├── services/
│       │   ├── fraudlens_client.py
│       │   ├── queue.py
│       │   ├── storage.py
│       │   └── notifications.py
│       └── database/
│           └── repositories/
│
└── docker-compose.yml
```

---

## 🔧 Development

### Run Locally (without Docker)

**Terminal 1: FraudLens API**
```bash
cd fraudlens
pip install -r requirements.txt
python -m uvicorn backend.api.main:app --reload
```

**Terminal 2: Redis**
```bash
redis-server
```

**Terminal 3: MinIO**
```bash
minio server ./data --console-address ":9001"
```

**Terminal 4: RQ Worker**
```bash
cd truthsnap-bot
pip install -r requirements.txt
rq worker high default low
```

**Terminal 5: Bot**
```bash
cd truthsnap-bot
export TELEGRAM_BOT_TOKEN="your_token"
python -m app.bot.main
```

---

## 🧪 Testing

### Test FraudLens API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Upload test photo
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@test_photo.jpg" \
  -F "detail_level=basic"
```

### Test Bot Flow

1. Send photo to bot
2. Check RQ Dashboard: http://localhost:9181
3. Watch worker logs: `docker-compose logs -f truthsnap-worker`
4. Verify result arrives in Telegram

---

## 📊 Monitoring

- **RQ Dashboard**: http://localhost:9181
- **MinIO Console**: http://localhost:9001 (user: minioadmin, pass: minioadmin)
- **Logs**: `docker-compose logs -f <service>`

---

## 🔒 Security Features

### Rate Limiting
- 5 messages/minute per user
- Prevents spam attacks

### Adversarial Protection
- Detects pixel-shifted photos
- Flags suspicious upload patterns

### Privacy
- Photos deleted after analysis
- No permanent storage

---

## 🎭 User Scenarios

### 👤 Adult Blackmail Scenario

**For adults being blackmailed with alleged intimate photos**

**Flow:**
1. Photo analysis with forensic evidence (SHA-256 hash, Report ID)
2. Generate legal-grade PDF report
3. Counter-measures:
   - Safe Response Generator (AI-crafted responses)
   - Links to StopNCII, FBI IC3
   - Educational resources

**Tone:** Cold, clinical, professional, legal-focused

### 🆘 Teenager SOS Scenario

**For teenagers facing sextortion**

**Flow:**
1. Psychological stop message ("Breathe. You are safe.")
2. Photo analysis with empathetic language
3. How to tell parents (conversation scripts)
4. Emergency protection:
   - Take It Down (NCMEC anonymous removal)
   - FBI Tips for Teens
   - CyberTipline reporting

**Tone:** Empathetic, supportive, educational

---

## 💎 Subscription Tiers

### Free
- 3 checks/day
- Basic verdict
- 20-30 sec processing
- Scenario-based support

### Pro ($9.99/mo)
- Unlimited checks
- Detailed forensic reports
- PDF downloads
- Priority processing (10-15 sec)
- All scenario features

---

## 🚀 Deployment

### Production (Railway/Fly.io/Render)

1. Create services:
   - FraudLens API (web service)
   - TruthSnap Bot (worker service)
   - RQ Workers (worker service, 3 instances)
   - Redis (managed Redis)
   - MinIO or AWS S3

2. Set environment variables

3. Deploy:
```bash
# Railway
railway up

# Fly.io
fly deploy

# Render
# Use render.yaml (see docs)
```

---

## 📝 TODO

### MVP (Week 1-2) ✅
- [x] FraudLens consumer endpoint
- [x] Bot handlers (start, photo, subscription)
- [x] RQ workers
- [x] S3 storage
- [x] Rate limiting
- [x] Adversarial protection

### Phase 2 (Week 3-4) ✅
- [x] Scenario-based flows (Adult Blackmail + Teenager SOS)
- [x] PDF report generation with forensic evidence
- [x] Counter-measures module
- [x] Parent communication helper
- [x] Knowledge Base
- [x] Watermark detection (SynthID, C2PA)
- [x] PostgreSQL database
- [ ] Stripe integration
- [ ] Analytics dashboard

### Phase 3 (Month 2)
- [ ] Multi-language support
- [ ] Batch processing
- [ ] API for partners
- [ ] Mobile app (React Native)

---

## 🆘 Support

- **Email**: support@truthsnap.ai
- **Twitter**: @TruthSnapBot
- **Telegram**: @TruthSnapSupport

---

## 📄 License

Proprietary - All rights reserved

---

## 🎯 Metrics Goals (Month 1)

- **Users**: 1,000
- **Premium**: 50 ($500 MRR)
- **Analyses**: 5,000
- **Accuracy**: 95%+
- **Uptime**: 99%+

---

**Built with ❤️ to fight deepfake blackmail**
