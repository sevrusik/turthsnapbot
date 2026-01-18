# 🔧 Developer Guide - TruthSnap Bot

**Complete development documentation for contributing to TruthSnap**

---

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Adding Features](#adding-features)
- [Testing](#testing)
- [Debugging](#debugging)
- [Best Practices](#best-practices)
- [Contributing](#contributing)

---

## 🚀 Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend, future)
- Git
- Telegram Bot Token

### Local Development (Without Docker)

**Terminal 1: PostgreSQL**
```bash
docker run -d --name truthsnap-postgres \
  -e POSTGRES_DB=truthsnap \
  -e POSTGRES_USER=truthsnap \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 postgres:16-alpine
```

**Terminal 2: Redis**
```bash
docker run -d --name truthsnap-redis \
  -p 6379:6379 redis:7-alpine
```

**Terminal 3: MinIO**
```bash
docker run -d --name truthsnap-minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 -p 9001:9001 \
  minio/minio server /data --console-address ":9001"
```

**Terminal 4: FraudLens API**
```bash
cd fraudlens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

**Terminal 5: RQ Worker**
```bash
cd truthsnap-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
rq worker high default low --url redis://localhost:6379/0
```

**Terminal 6: Telegram Bot**
```bash
cd truthsnap-bot
source .venv/bin/activate
export TELEGRAM_BOT_TOKEN="your_token"
export FRAUDLENS_API_URL="http://localhost:8000"
python -m app.bot.main
```

### With Docker (Recommended)

```bash
# Clone repo
git clone <repo-url>
cd TruthSnapBot

# Configure
cp .env.example .env
nano .env  # Add your TELEGRAM_BOT_TOKEN

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

---

## 📁 Project Structure

```
TruthSnapBot/
├── fraudlens/                      # Detection API Service
│   ├── backend/
│   │   ├── api/
│   │   │   ├── main.py            # FastAPI app entry
│   │   │   └── routes/
│   │   │       └── consumer.py     # /verify endpoint
│   │   ├── core/
│   │   │   └── fraud_detector.py   # Main detection logic
│   │   ├── integrations/
│   │   │   ├── fft_detector.py     # FFT analysis (optimized)
│   │   │   ├── metadata.py         # EXIF metadata
│   │   │   ├── watermark_detector.py
│   │   │   ├── simple_detector.py
│   │   │   ├── face_swap_detector.py
│   │   │   └── metadata_validator.py
│   │   └── models/
│   │       └── consumer.py         # Pydantic models
│   ├── Dockerfile
│   └── requirements.txt
│
├── truthsnap-bot/                  # Telegram Bot Service
│   ├── app/
│   │   ├── bot/
│   │   │   ├── main.py            # Bot entry point
│   │   │   ├── handlers/
│   │   │   │   ├── start.py       # /start, /help
│   │   │   │   ├── scenarios.py   # 🆕 Scenario flows (Adult/Teenager)
│   │   │   │   ├── counter_measures.py # 🆕 Adult counter-measures
│   │   │   │   ├── parent_support.py   # 🆕 Teenager parent helper
│   │   │   │   ├── photo.py       # Photo upload handling
│   │   │   │   ├── subscription.py # /subscribe
│   │   │   │   └── callbacks.py    # Callback queries (PDF reports)
│   │   │   ├── keyboards/
│   │   │   │   └── scenarios.py   # 🆕 Scenario inline keyboards
│   │   │   ├── middlewares/
│   │   │   │   ├── rate_limit.py   # 5 msg/min limit
│   │   │   │   ├── adversarial.py  # Attack detection
│   │   │   │   └── logging.py      # Request logging
│   │   │   └── states.py          # 🆕 FSM states (Scenario-based)
│   │   ├── workers/
│   │   │   └── tasks.py           # Background jobs (RQ)
│   │   ├── services/
│   │   │   ├── fraudlens_client.py # API client
│   │   │   ├── queue.py            # Job queue
│   │   │   ├── storage.py          # S3 operations
│   │   │   ├── notifications.py    # User notifications
│   │   │   └── image_validator.py  # Image validation
│   │   ├── database/
│   │   │   └── repositories/
│   │   │       ├── user_repo.py
│   │   │       └── analysis_repo.py
│   │   └── config/
│   │       └── settings.py        # Configuration
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/                          # Documentation
│   ├── API_REFERENCE.md
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md         # This file
│   ├── ARCHITECTURE.md
│   └── FFT_OPTIMIZATION.md
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## 🔌 Core Components

### 1. FraudLens API (FastAPI)

**Entry Point**: `fraudlens/backend/api/main.py`

```python
from fastapi import FastAPI
from backend.api.routes import consumer

app = FastAPI(title="FraudLens API")
app.include_router(consumer.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}
```

**Main Endpoint**: `fraudlens/backend/api/routes/consumer.py`

```python
@router.post("/consumer/verify")
async def verify_image(
    image: UploadFile,
    detail_level: str = "basic"
):
    # 1. Validate image
    # 2. Run detection
    # 3. Return results
    pass
```

### 2. Telegram Bot (aiogram 3.x)

**Entry Point**: `truthsnap-bot/app/bot/main.py`

```python
from aiogram import Bot, Dispatcher
from app.bot.handlers import (
    start, scenarios, counter_measures,
    parent_support, photo, subscription, callbacks
)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=RedisStorage(...))  # For FSM states

    # Register handlers - ORDER MATTERS!
    dp.include_router(start.router)              # /start command (FIRST!)
    dp.include_router(subscription.router)       # Subscription management
    dp.include_router(scenarios.router)          # Scenario-based flows
    dp.include_router(counter_measures.router)   # Adult counter-measures
    dp.include_router(parent_support.router)     # Teenager support
    dp.include_router(callbacks.router)          # PDF reports
    dp.include_router(photo.router)              # Legacy handlers (LAST!)

    await dp.start_polling(bot)
```

**FSM States**: `truthsnap-bot/app/bot/states.py`

```python
from aiogram.fsm.state import State, StatesGroup

class ScenarioStates(StatesGroup):
    selecting_scenario = State()  # Initial scenario selection

class AdultBlackmailStates(StatesGroup):
    waiting_for_evidence = State()  # Waiting for photo
    reviewing_analysis = State()    # Analysis complete
    counter_measures = State()      # Counter-measures menu

class TeenagerSOSStates(StatesGroup):
    psychological_stop = State()    # Calming message
    waiting_for_photo = State()     # Waiting for photo
    ally_search = State()           # Parent communication
    emergency_protection = State()  # Take It Down, reporting
```

### 3. Background Workers (RQ)

**Task Definition**: `truthsnap-bot/app/workers/tasks.py`

```python
def analyze_photo_task(user_id, photo_url, job_id):
    """Background task for photo analysis"""
    try:
        # 1. Download from S3
        # 2. Call FraudLens API
        # 3. Save result
        # 4. Notify user
        # 5. Cleanup S3
    except Exception as e:
        # Error handling
        pass
```

---

## ➕ Adding Features

### Adding a New Bot Command

**1. Create handler** in `truthsnap-bot/app/bot/handlers/`:

```python
# my_command.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("mycommand"))
async def my_command_handler(message: Message):
    await message.answer("Hello from my command!")
```

**2. Register in** `main.py`:

```python
from app.bot.handlers import my_command

dp.include_router(my_command.router)
```

**3. Test**:
```bash
# Restart bot
docker-compose restart truthsnap-bot

# In Telegram, send: /mycommand
```

### Adding a New Detection Layer

**1. Create detector** in `fraudlens/backend/integrations/`:

```python
# my_detector.py
import logging

logger = logging.getLogger(__name__)

class MyDetector:
    def __init__(self):
        self.enabled = True

    async def analyze(self, image_bytes: bytes) -> dict:
        """
        Analyze image for specific artifacts

        Returns:
            {
                "score": 0.0-1.0,  # Higher = more likely AI
                "checks": [...],
                "details": {...}
            }
        """
        try:
            # Your detection logic here
            score = 0.5

            return {
                "score": score,
                "checks": [{
                    "layer": "My Detection",
                    "status": "PASS" if score < 0.6 else "FAIL",
                    "score": score,
                    "reason": "Detection reason",
                    "confidence": 0.85
                }],
                "details": {}
            }
        except Exception as e:
            logger.error(f"My detector failed: {e}")
            return {"score": 0.5, "checks": [], "details": {}}
```

**2. Integrate in** `fraud_detector.py`:

```python
from backend.integrations.my_detector import MyDetector

class FraudDetector:
    def __init__(self):
        self.my_detector = MyDetector()

    async def analyze(self, image_bytes, detail_level):
        # ... existing code ...

        # Add your detector
        my_result = await self.my_detector.analyze(image_bytes)
        all_checks.extend(my_result["checks"])

        # Update overall score
        overall_score = (existing_score + my_result["score"]) / 2

        return result
```

**3. Test**:
```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@test.jpg" \
  -F "detail_level=detailed" \
  | jq '.detection_layers'
```

### Adding a New Middleware

**1. Create middleware** in `truthsnap-bot/app/bot/middlewares/`:

```python
# my_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import Message

class MyMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        # Before handler
        print(f"Before: {event.text}")

        # Call handler
        result = await handler(event, data)

        # After handler
        print(f"After: {event.text}")

        return result
```

**2. Register in** `main.py`:

```python
from app.bot.middlewares.my_middleware import MyMiddleware

dp.message.middleware(MyMiddleware())
```

### Adding a New Scenario

**1. Define states** in `bot/states.py`:

```python
class MyNewScenarioStates(StatesGroup):
    initial_message = State()
    waiting_for_input = State()
    showing_results = State()
```

**2. Create keyboard** in `bot/keyboards/scenarios.py`:

```python
def get_my_scenario_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for my new scenario"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔥 Action 1",
            callback_data="my_scenario:action1"
        )],
        [InlineKeyboardButton(
            text="🔙 Back to Main Menu",
            callback_data="scenario:select"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
```

**3. Add scenario entry** in `scenarios.py`:

```python
@router.callback_query(F.data == "scenario:my_new_scenario")
async def my_new_scenario(callback: CallbackQuery, state: FSMContext):
    """Entry point for my new scenario"""
    await callback.message.edit_text(
        "🔥 <b>My New Scenario</b>\n\n"
        "Welcome to my scenario flow!",
        parse_mode="HTML",
        reply_markup=get_my_scenario_keyboard()
    )

    await state.set_state(MyNewScenarioStates.initial_message)
    await callback.answer()
```

**4. Add to main menu** in `get_scenario_selection_keyboard()`:

```python
[InlineKeyboardButton(
    text="🔥 My New Scenario",
    callback_data="scenario:my_new_scenario"
)]
```

**5. Propagate scenario context** through queue:

```python
# In your photo handler
scenario = "my_new_scenario"

job_id = queue_service.enqueue_analysis(
    user_id=user_id,
    chat_id=chat_id,
    message_id=message_id,
    photo_s3_key=s3_key,
    tier=tier,
    scenario=scenario  # Pass scenario to worker
)
```

**6. Add scenario-specific response** in `notifications.py`:

```python
elif scenario == "my_new_scenario":
    keyboard = [
        [InlineKeyboardButton(text="🔥 Action 1", callback_data="my_scenario:action1")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="scenario:select")]
    ]
```

---

## 🧪 Testing

### Unit Tests

```bash
cd fraudlens
pytest tests/test_fft_detector.py -v
pytest tests/test_metadata.py -v
```

### Integration Tests

```bash
cd truthsnap-bot
pytest tests/test_photo_flow.py -v
```

### Manual Testing

See `TESTING.md` for comprehensive test suite (27 tests).

### Performance Testing

```bash
# FFT performance
docker exec fraudlens-api python3 /app/test_fft_performance.py

# Load testing
ab -n 1000 -c 10 -p test_image.jpg \
  http://localhost:8000/api/v1/consumer/verify
```

---

## 🐛 Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f truthsnap-bot
docker-compose logs -f fraudlens-api
docker-compose logs -f truthsnap-worker

# Last 100 lines
docker-compose logs --tail=100 truthsnap-bot
```

### Interactive Debugging

**Bot debugging**:
```python
# Add to handler
import pdb; pdb.set_trace()

# Or use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable: {my_var}")
```

**API debugging**:
```python
# In FastAPI endpoint
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Request: {request}")
```

### Common Issues

**Bot not receiving updates:**
```bash
# Check webhook conflicts
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Delete webhook if exists
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

**Worker not processing jobs:**
```bash
# Check Redis connection
redis-cli -h localhost ping

# Check RQ Dashboard
open http://localhost:9181

# Manually clear failed jobs
rq requeue --all
```

**API connection refused:**
```bash
# Check if API is running
curl http://localhost:8000/api/v1/health

# Check Docker networks
docker network inspect truthsnapbot_default
```

---

## ✅ Best Practices

### Code Style

**Python (PEP 8)**:
```python
# Good
async def analyze_photo(user_id: int, photo_url: str) -> dict:
    """Analyze photo for AI detection"""
    result = await fraudlens_client.verify(photo_url)
    return result

# Bad
async def AnalyzePhoto(userID,photoURL):
    result=await fraudlens_client.verify(photoURL)
    return result
```

**Type Hints**:
```python
from typing import Dict, Optional

async def get_user(user_id: int) -> Optional[Dict]:
    """Always use type hints"""
    return user_repo.find_by_id(user_id)
```

### Error Handling

**Always catch specific exceptions**:
```python
# Good
try:
    result = await api_call()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    return {"error": "API unavailable"}
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    return {"error": "Invalid input"}

# Bad
try:
    result = await api_call()
except:
    return {"error": "Something went wrong"}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed info for debugging")
logger.info("Important events")
logger.warning("Warning conditions")
logger.error("Error conditions")
logger.critical("Critical failures")

# Include context
logger.info(f"User {user_id} uploaded photo {photo_id}")
logger.error(f"API call failed for user {user_id}: {error}")
```

### Security

**Never log sensitive data**:
```python
# Bad
logger.info(f"User token: {user_token}")

# Good
logger.info(f"User authenticated: user_id={user_id}")
```

**Validate all inputs**:
```python
def validate_image(file: UploadFile):
    # Check file size
    if file.size > 20 * 1024 * 1024:
        raise ValueError("File too large")

    # Check mime type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise ValueError("Invalid file type")

    return True
```

### Performance

**Use async/await properly**:
```python
# Good - parallel
results = await asyncio.gather(
    api_call_1(),
    api_call_2(),
    api_call_3()
)

# Bad - sequential
result1 = await api_call_1()
result2 = await api_call_2()
result3 = await api_call_3()
```

**Cache expensive operations**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(param):
    return result
```

---

## 🤝 Contributing

### Workflow

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/my-feature`
3. **Make** changes and commit: `git commit -am 'Add feature'`
4. **Push** to branch: `git push origin feature/my-feature`
5. **Open** Pull Request

### Pull Request Guidelines

**Title**: Clear, concise description
```
✅ Add watermark detection for SynthID
❌ Update code
```

**Description**: Include:
- What changed
- Why it changed
- How to test
- Screenshots (if UI)

**Checklist**:
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Tested locally

### Code Review

**Reviewers check for**:
- Code quality
- Test coverage
- Security issues
- Performance impact
- Documentation

---

## 📚 Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [aiogram Docs](https://docs.aiogram.dev/)
- [RQ Docs](https://python-rq.org/)
- [Docker Docs](https://docs.docker.com/)

### Internal Docs
- [API Reference](./API_REFERENCE.md)
- [User Guide](./USER_GUIDE.md)
- [Architecture](./ARCHITECTURE.md)
- [FFT Optimization](./FFT_OPTIMIZATION.md)

### Contact
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: dev@truthsnap.ai

---

**Happy coding! 🚀**
