# ⚡ QUICKSTART БЕЗ DOCKER - TruthSnap Bot

Запуск TruthSnap Bot локально на Mac **без Docker**.

---

## 📋 Что нужно установить

### 1. Homebrew (если еще нет)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python 3.11
```bash
brew install python@3.11
```

### 3. Redis
```bash
brew install redis
```

### 4. MinIO (опционально, для S3 storage)
```bash
brew install minio/stable/minio
```

---

## 🚀 Запуск (3 минуты)

### Шаг 1: Получить токен бота

1. Открой Telegram
2. Найди **@BotFather**
3. Отправь `/newbot`
4. Следуй инструкциям
5. Скопируй токен (например: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Настроить проект

```bash
# Перейди в папку проекта
cd /Volumes/KINGSTON/Projects/TruthSnapBot

# Создай .env файл
cp .env.example .env

# Открой .env и добавь свой токен
nano .env
```

В файле `.env` измени:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```
на свой реальный токен:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 3: Запустить бота

```bash
make local-start
```

Скрипт автоматически:
- ✅ Создаст виртуальное окружение Python
- ✅ Установит все зависимости
- ✅ Запустит Redis
- ✅ Запустит FraudLens API
- ✅ Запустит MinIO (если установлен)
- ✅ Запустит 3 RQ workers
- ✅ Запустит Telegram bot

### Шаг 4: Тестировать!

1. Открой Telegram
2. Найди своего бота (имя из @BotFather)
3. Отправь `/start`
4. Загрузи фото
5. Жди 20-30 секунд
6. Получи результат! 🎉

---

## 📊 Мониторинг

### Посмотреть логи всех сервисов:
```bash
make local-logs
```

### Посмотреть логи отдельно:
```bash
# Бот
tail -f logs/bot.log

# API
tail -f logs/fraudlens.log

# Workers
tail -f logs/worker-1.log
tail -f logs/worker-2.log
tail -f logs/worker-3.log

# MinIO
tail -f logs/minio.log
```

### Открыть веб-интерфейсы:
```bash
# FraudLens API
open http://localhost:8000

# API документация
open http://localhost:8000/docs

# MinIO Console
open http://localhost:9001
# Логин: minioadmin
# Пароль: minioadmin
```

---

## 🛑 Остановить сервисы

```bash
make local-stop
```

Это остановит:
- ✅ Telegram bot
- ✅ FraudLens API
- ✅ RQ workers
- ✅ Redis
- ✅ MinIO

---

## 🐛 Проблемы?

### Бот не отвечает

```bash
# Проверь логи
tail -f logs/bot.log

# Если видишь ошибки, перезапусти
make local-stop
make local-start
```

### "Connection refused" ошибки

```bash
# Проверь, что Redis запущен
redis-cli ping
# Должно вывести: PONG

# Если не отвечает, запусти вручную:
redis-server --daemonize yes
```

### API не запускается

```bash
# Проверь логи
tail -f logs/fraudlens.log

# Проверь, что порт 8000 свободен
lsof -i :8000

# Если порт занят, останови процесс:
kill $(lsof -t -i:8000)
```

### Workers не обрабатывают задачи

```bash
# Проверь логи workers
tail -f logs/worker-*.log

# Перезапусти workers
make local-stop
make local-start
```

---

## 📦 Структура процессов

После запуска `make local-start` у тебя будет:

```
Redis Server (порт 6379)
    ↓
FraudLens API (порт 8000)
    ↓
3x RQ Workers (background)
    ↓
Telegram Bot (background)
    ↓
MinIO (порт 9000, 9001) [опционально]
```

Все процессы запущены в фоне (daemon mode).

PIDs сохранены в `.pids/` директории.

---

## 🔄 Обновить код

Если ты изменил код и хочешь перезапустить:

```bash
# Остановить
make local-stop

# Запустить снова
make local-start
```

---

## ✅ Проверить, что все работает

### 1. API Health Check
```bash
curl http://localhost:8000/api/v1/health
# Должно вывести: {"status":"healthy"}
```

### 2. Redis Check
```bash
redis-cli ping
# Должно вывести: PONG
```

### 3. Проверить процессы
```bash
ps aux | grep -E "(python|redis|rq|minio)"
```

Должны быть запущены:
- `redis-server`
- `python -m uvicorn` (FraudLens API)
- `python -m app.bot.main` (Bot)
- `rq worker` (3 процесса)
- `minio server` (если установлен)

---

## 💡 Полезные команды

```bash
# Посмотреть все команды
make help

# Запустить локально
make local-start

# Остановить
make local-stop

# Логи
make local-logs

# Только бот (для разработки)
make dev-bot

# Только API (для разработки)
make dev-api

# Только worker (для разработки)
make dev-worker
```

---

## 🎯 Что дальше?

1. ✅ Бот работает локально
2. 📸 Протестируй с 10 разными фото
3. 📊 Посмотри логи
4. 🔧 Измени код в `truthsnap-bot/app/bot/handlers/`
5. 🔄 Перезапусти: `make local-stop && make local-start`

---

## 📞 Нужна помощь?

Если что-то не работает:

1. **Проверь логи**: `make local-logs`
2. **Проверь .env**: Правильный ли токен?
3. **Перезапусти**: `make local-stop && make local-start`
4. **Открой issue** в GitHub

---

**🎉 Готово! Теперь у тебя работает TruthSnap Bot БЕЗ Docker!** 🎉

*Если хочешь использовать Docker:*
1. Установи Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Запусти: `make start`
