# 🔍 TruthSnapBot - Code Review Report

**Дата проверки:** 27 января 2026
**Архитектура:** Telegram Bot (aiogram 3.x) + Redis Queue + PostgreSQL + MinIO/S3
**Проверено файлов:** ~50 Python модулей

---

## 📊 Итоговая оценка: 7.0/10

### ✅ Сильные стороны
- Отличная модульная архитектура (handlers, services, middlewares)
- Сценарий-ориентированный дизайн (Adult Blackmail vs Teenager SOS)
- Комплексная валидация изображений (AI watermarks, screenshots, pHash)
- Правильное использование FSM states
- Безопасность SQL (параметризованные запросы)
- Хорошая документация в коде

### ⚠️ Требует улучшений
- **КРИТИЧНО:** Middlewares не зарегистрированы (не работают!)
- In-memory storage для rate limiting (нужен Redis)
- Синхронный S3 блокирует event loop
- Отсутствие unit tests
- Нет health checks
- Subscription logic отключена

---

## 🔴 Критические проблемы

### 1. Middlewares не зарегистрированы!

**Файл:** `truthsnap-bot/app/bot/main.py:56-67`

**Проблема:**
Middlewares реализованы, но НЕ зарегистрированы в Dispatcher. Rate limiting и adversarial protection **не работают**!

**Найденные middleware:**
- ✅ `middlewares/rate_limit.py` - RateLimitMiddleware (5 msg/min)
- ✅ `middlewares/adversarial.py` - AdversarialProtectionMiddleware
- ✅ `middlewares/logging.py` - LoggingMiddleware

**Решение:**
```python
# В main.py после строки 57 добавить:
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.adversarial import AdversarialProtectionMiddleware
from bot.middlewares.logging import LoggingMiddleware

# Регистрация middleware (порядок важен!)
dp.message.middleware(LoggingMiddleware())
dp.message.middleware(RateLimitMiddleware(
    rate_limit=settings.RATE_LIMIT_PER_MINUTE,
    window=60
))
dp.message.middleware(AdversarialProtectionMiddleware(
    similarity_threshold=settings.ADVERSARIAL_SIMILARITY_THRESHOLD,
    max_similar=settings.ADVERSARIAL_MAX_SIMILAR_UPLOADS,
    window_hours=settings.ADVERSARIAL_WINDOW_HOURS
))
```

---

### 2. Rate Limiting использует in-memory storage

**Файл:** `middlewares/rate_limit.py:32`

**Проблема:**
```python
self.user_requests: Dict[int, list] = {}  # In-memory!
```
- При перезапуске бота данные теряются
- Не работает при horizontal scaling
- Может быть обойден через reconnect

**Решение:**
```python
import redis.asyncio as redis

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis_url: str, rate_limit: int = 5, window: int = 60):
        self.redis = redis.from_url(redis_url)
        self.rate_limit = rate_limit
        self.window = window

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        key = f"rate_limit:{user_id}"

        # Atomic increment with TTL
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)

        if count > self.rate_limit:
            await event.answer("⚠️ Too many requests. Please wait.", show_alert=True)
            return

        return await handler(event, data)
```

---

### 3. Adversarial Protection легко обойти

**Файл:** `middlewares/adversarial.py:58`

**Проблема:**
```python
file_hash = photo.file_unique_id  # Меняется при любом изменении пикселя
```
Атакующий может добавить 1px шум и обойти защиту.

**Решение (использовать perceptual hash):**
```python
from services.image_validator import ImageValidator
import io

class AdversarialProtectionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not event.photo:
            return await handler(event, data)

        # Download photo
        file = await event.bot.get_file(event.photo[-1].file_id)
        file_bytes = io.BytesIO()
        await event.bot.download_file(file.file_path, file_bytes)

        # Calculate perceptual hash (устойчив к шуму)
        validator = ImageValidator()
        report = await validator.validate(file_bytes.getvalue())
        phash = report.phash

        # Store in Redis with TTL
        key = f"adversarial:{event.from_user.id}:{phash}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 3600)

        if count > 10:
            await event.answer("🚨 Adversarial attack detected", show_alert=True)
            return

        return await handler(event, data)
```

---

### 4. S3 Storage синхронный (блокирует event loop)

**Файл:** `services/storage.py:52-78`

**Проблема:**
```python
async def upload(self, data: bytes, key: str) -> str:
    self.s3_client.put_object(...)  # ← Синхронный вызов в async функции!
```

**Решение (использовать aioboto3):**
```bash
pip install aioboto3
```

```python
import aioboto3
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket = settings.S3_BUCKET

    async def upload(self, data: bytes, key: str) -> str:
        """Async upload to S3"""
        async with self.session.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        ) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType='image/jpeg'
            )
            return f"s3://{self.bucket}/{key}"

    async def download(self, key: str) -> bytes:
        """Async download from S3 with retry"""
        async with self.session.client(...) as s3:
            for attempt in range(3):
                try:
                    response = await s3.get_object(Bucket=self.bucket, Key=key)
                    return await response['Body'].read()
                except ClientError as e:
                    if attempt == 2:
                        raise S3DownloadError(f"Failed: {e}")
                    await asyncio.sleep(2 ** attempt)
```

---

### 5. Множественные event loops в Worker

**Файл:** `workers/tasks.py:67, 92, 126, 134`

**Проблема:**
```python
asyncio.run(s3.download(...))  # Создает новый event loop
asyncio.run(fraudlens.verify_photo(...))  # Еще один
asyncio.run(analysis_repo.create_analysis(...))  # И еще
```
Неэффективно - каждый `asyncio.run()` создает/удаляет event loop.

**Решение:**
```python
async def analyze_photo_task_async(
    user_id: int,
    chat_id: int,
    message_id: int,
    photo_s3_key: str,
    tier: str,
    scenario: str = None
):
    """Async version - single event loop"""
    try:
        # Download from S3
        s3 = S3Storage()
        photo_bytes = await s3.download(photo_s3_key)

        # Analyze with timeout
        fraudlens = FraudLensClient()
        async with asyncio.timeout(30):
            result = await fraudlens.verify_photo(photo_bytes, ...)

        # Save to DB
        analysis_repo = AnalysisRepository()
        analysis_id = await analysis_repo.create_analysis(...)

        # Notify user
        notifier = BotNotifier()
        await notifier.send_analysis_result(...)

        logger.info(f"✅ Analysis complete: {analysis_id}")

    except asyncio.TimeoutError:
        logger.error("FraudLens API timeout")
        raise AnalysisTimeoutError("Analysis took too long")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

def analyze_photo_task(*args, **kwargs):
    """Wrapper for RQ (synchronous)"""
    return asyncio.run(analyze_photo_task_async(*args, **kwargs))
```

---

## 🟡 Высокий приоритет

### 6. Отсутствие unit tests

**Проблема:** Нет файлов `test_*.py`

**Решение:**
```bash
pip install pytest pytest-asyncio
```

```python
# tests/test_image_validator.py
import pytest
from services.image_validator import ImageValidator, ValidationResult

@pytest.mark.asyncio
async def test_ai_detection():
    """Test AI-generated image detection"""
    validator = ImageValidator()

    with open('tests/fixtures/midjourney_fake.jpg', 'rb') as f:
        result = await validator.validate(f.read())

    assert result.result == ValidationResult.AI_GENERATED
    assert not result.is_valid
    assert 'midjourney' in result.reason.lower()

@pytest.mark.asyncio
async def test_screenshot_detection():
    """Test screenshot detection"""
    validator = ImageValidator()

    with open('tests/fixtures/screenshot.png', 'rb') as f:
        result = await validator.validate(f.read())

    assert result.result == ValidationResult.SCREENSHOT
    assert not result.is_valid

@pytest.mark.asyncio
async def test_heic_conversion():
    """Test HEIC to JPEG conversion"""
    validator = ImageValidator()

    with open('tests/fixtures/iphone.heic', 'rb') as f:
        result = await validator.validate(f.read())

    # Should convert successfully
    assert result.is_valid or result.result == ValidationResult.REAL
```

---

### 7. Subscription logic отключена

**Файл:** `database/repositories/user_repo.py:106-156`

**Проблема:**
```python
async def can_user_analyze(self, telegram_id: int) -> Tuple[bool, Optional[str]]:
    # TEMPORARILY DISABLED: No subscription checks
    return True, None  # ← ВСЕГДА разрешает!
```

**Риски:**
- Любой пользователь = unlimited uploads
- Нет монетизации
- Риск DDoS / злоупотребления

**Решение:**
```python
async def can_user_analyze(self, telegram_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user can perform analysis"""
    user = await self.get_user(telegram_id)

    if not user:
        # New user - allow first 3 free analyses
        return True, None

    # Check subscription tier
    if user['tier'] == 'pro':
        return True, None

    # Free tier - check daily limit
    today = datetime.now().date()
    count = await self.get_daily_analysis_count(telegram_id, today)

    if count >= 3:
        return False, (
            "❌ Daily limit reached (3/day).\n\n"
            "Upgrade to Pro for unlimited analyses:\n"
            "/upgrade"
        )

    return True, None
```

---

### 8. Нет health checks

**Решение:**
```python
# bot/handlers/admin.py (новый файл)
from aiogram import Router
from aiogram.filters import Command

router = Router()

@router.message(Command("health"))
async def health_check(message: Message):
    """Health check for admins"""
    if message.from_user.id not in settings.ADMIN_USER_IDS:
        return

    checks = {}

    # Check database
    try:
        from database.db import db
        await db.fetchval("SELECT 1")
        checks['database'] = '✅'
    except:
        checks['database'] = '❌'

    # Check Redis
    try:
        from redis.asyncio import Redis
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        checks['redis'] = '✅'
    except:
        checks['redis'] = '❌'

    # Check S3
    try:
        from services.storage import S3Storage
        s3 = S3Storage()
        checks['s3'] = '✅'
    except:
        checks['s3'] = '❌'

    # Check FraudLens API
    try:
        from services.fraudlens_client import FraudLensClient
        client = FraudLensClient()
        result = await client.health_check()
        checks['fraudlens'] = '✅'
    except:
        checks['fraudlens'] = '❌'

    text = "<b>🏥 Health Check</b>\n\n"
    for service, status in checks.items():
        text += f"{status} {service.title()}\n"

    await message.answer(text, parse_mode="HTML")
```

---

### 9. Дефолтные credentials в .env.example

**Файл:** `.env.example`

**Проблема:**
```bash
MINIO_ACCESS_KEY=minioadmin  # Небезопасно!
MINIO_SECRET_KEY=minioadmin
```

**Решение:**
```bash
# .env.example
# ⚠️ SECURITY: Change ALL default credentials in production!
# Use strong passwords (min 16 characters, alphanumeric + symbols)

TELEGRAM_BOT_TOKEN=your_bot_token_here  # Get from @BotFather
ADMIN_USER_IDS=123456789  # Comma-separated admin IDs

# MinIO (S3) - CHANGE THESE!
MINIO_ACCESS_KEY=generate_random_32_chars  # Use: openssl rand -hex 16
MINIO_SECRET_KEY=generate_random_64_chars  # Use: openssl rand -hex 32

# Database - CHANGE THIS!
DATABASE_URL=postgresql://truthsnap:STRONG_PASSWORD@localhost:5432/truthsnap

# Redis - ENABLE AUTH!
REDIS_URL=redis://:STRONG_PASSWORD@localhost:6379/0

# Secret Key
SECRET_KEY=generate_random_64_chars  # Use: openssl rand -hex 32
```

---

### 10. Retry логика для Queue

**Файл:** `services/queue.py:71-88`

**Проблема:** Нет retry если job fails

**Решение:**
```python
from rq.retry import Retry

job = queue.enqueue(
    'app.workers.tasks.analyze_photo_task',
    user_id=user_id,
    chat_id=chat_id,
    message_id=message_id,
    photo_s3_key=photo_s3_key,
    tier=tier,
    scenario=scenario,
    job_timeout='5m',
    result_ttl=3600,
    failure_ttl=86400,
    retry=Retry(max=3, interval=[10, 30, 60])  # Retry 3 times: 10s, 30s, 60s
)
```

---

## 🟢 Средний приоритет

### 11. PII в логах

**Файл:** `handlers/scenarios.py:162`

**Проблема:**
```python
logger.info(f"Photo received from user {user_id}")  # user_id = PII
```

**Решение:**
```python
import hashlib

def anonymize_user_id(user_id: int) -> str:
    """Hash user_id for logs (GDPR compliance)"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]

# Usage:
logger.info(f"Photo received from user {anonymize_user_id(user_id)}")
```

---

### 12. S3 Lifecycle Policy

**Проблема:** Файлы накапливаются в S3 (24h+ хранение)

**Решение (MinIO/S3 lifecycle policy):**
```xml
<!-- Автоматически удалять файлы через 24 часа -->
<LifecycleConfiguration>
  <Rule>
    <ID>auto-delete-temp-photos</ID>
    <Filter>
      <Prefix>temp/</Prefix>
    </Filter>
    <Status>Enabled</Status>
    <Expiration>
      <Days>1</Days>
    </Expiration>
  </Rule>
</LifecycleConfiguration>
```

```bash
# Применить через mc (MinIO Client):
mc ilm add myminio/truthsnap --expiry-days 1 --prefix "temp/"
```

---

### 13. Обработка ошибок слишком общая

**Файл:** `handlers/callbacks.py:134`

**Проблема:**
```python
except Exception as e:  # Слишком общий except
    logger.error(f"PDF generation failed: {e}")
```

**Решение:**
```python
# Определить кастомные исключения:
class AnalysisNotFoundError(Exception):
    pass

class UnauthorizedAccessError(Exception):
    pass

class S3DownloadError(Exception):
    pass

class PDFGenerationError(Exception):
    pass

# В handlers:
try:
    # ... existing code ...
except AnalysisNotFoundError:
    await callback.answer("❌ Analysis not found", show_alert=True)
except UnauthorizedAccessError:
    await callback.answer("❌ Unauthorized", show_alert=True)
except S3DownloadError:
    await callback.answer("❌ Photo expired", show_alert=True)
except PDFGenerationError as e:
    await callback.answer(f"❌ PDF failed: {e}", show_alert=True)
except Exception as e:
    logger.error(f"Unexpected: {e}", exc_info=True)
    await callback.answer("❌ System error", show_alert=True)
```

---

## ✅ Положительные моменты

### Что сделано отлично:

1. **Архитектура** - Чистая модульная структура, separation of concerns
2. **Валидация изображений** - Комплексная проверка (AI watermarks, screenshots, HEIC, pHash)
3. **Сценарии** - Два разных тона (клинический vs эмпатичный) - отлично!
4. **FSM States** - Правильное использование aiogram 3.x states
5. **SQL безопасность** - Параметризованные запросы, нет SQL injection
6. **Документация** - Хорошие docstrings и комментарии
7. **Keyboard layouts** - Интуитивные inline keyboards
8. **Error messages** - Понятные сообщения для пользователей
9. **Async/await** - Правильное использование (кроме S3)
10. **Logging** - Подробное логирование (66+ вызовов)

---

## 📋 Чек-лист для production

### 🔴 Критические (блокируют деплой)
- [ ] Зарегистрировать middlewares в main.py
- [ ] Переписать rate limiting на Redis
- [ ] Переписать adversarial protection на pHash + Redis
- [ ] Переписать S3 на aioboto3 (async)
- [ ] Рефакторить worker task (один async flow)

### 🟡 Высокие (исправить до релиза)
- [ ] Добавить unit tests (минимум 10 тестов)
- [ ] Включить subscription logic ИЛИ добавить жесткий rate limit
- [ ] Добавить health check endpoint
- [ ] Изменить дефолтные credentials в .env.example
- [ ] Добавить retry в queue

### 🟢 Средние (желательно)
- [ ] Анонимизация user_id в логах
- [ ] Настроить S3 lifecycle policy
- [ ] Улучшить обработку ошибок (кастомные исключения)
- [ ] Добавить мониторинг очереди
- [ ] Добавить метрики (Prometheus)

---

## 📚 Дополнительные рекомендации

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

### Мониторинг
```python
# Добавить Sentry для error tracking
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1
)
```

### Docker Compose для локальной разработки
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
```

---

## 🎯 Приоритетный план (4 недели)

### Неделя 1 (Критичные):
1. ✅ Зарегистрировать middlewares
2. ✅ Переписать rate limiting на Redis
3. ✅ Переписать adversarial на pHash + Redis
4. ✅ Добавить unit tests (минимум image_validator)

### Неделя 2 (Высокие):
1. ✅ Переписать S3 на aioboto3
2. ✅ Рефакторить worker (async flow)
3. ✅ Добавить retry в queue
4. ✅ Health check endpoint

### Неделя 3 (Средние):
1. ✅ Включить subscription logic
2. ✅ Анонимизация PII в логах
3. ✅ S3 lifecycle policy
4. ✅ Обновить .env.example

### Неделя 4 (Production):
1. ✅ CI/CD pipeline
2. ✅ Мониторинг (Sentry)
3. ✅ Load testing
4. ✅ Security audit

---

## 🎖️ Финальная оценка

**Общая оценка: 7/10**

| Категория | Оценка | Комментарий |
|-----------|--------|-------------|
| Архитектура | 9/10 | Отличная модульность |
| Безопасность | 5/10 | Middlewares не работают! |
| Валидация | 9/10 | Комплексная проверка |
| Error Handling | 7/10 | Хорошо, но можно улучшить |
| Performance | 6/10 | Sync S3 блокирует loop |
| Testing | 2/10 | Нет unit tests |
| Documentation | 8/10 | Хорошие docstrings |
| Maintainability | 8/10 | Чистый код |

**После исправлений оценка: 8.5/10** ⭐

---

## 📞 Заключение

**TruthSnapBot** - хорошо спроектированный бот с чистой архитектурой и отличными сценариями для помощи жертвам deepfake blackmail.

**Основные проблемы:**
1. 🔴 Middlewares не работают (не зарегистрированы)
2. 🔴 Rate limiting и adversarial protection in-memory
3. 🔴 Синхронный S3 блокирует event loop
4. 🟡 Нет tests и health checks

**После исправления критичных проблем бот будет production-ready.**

Рекомендуется начать с Недели 1 чек-листа и протестировать каждое изменение перед деплоем.
