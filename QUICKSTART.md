# ⚡ QUICKSTART - TruthSnap Bot

Get up and running in **5 minutes**.

---

## Step 1: Get Telegram Bot Token

1. Open Telegram
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow prompts
5. Copy your bot token (looks like `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

## Step 2: Configure

```bash
# Create .env file
echo "TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE" > .env
echo "MINIO_ACCESS_KEY=minioadmin" >> .env
echo "MINIO_SECRET_KEY=minioadmin" >> .env
```

Replace `YOUR_TOKEN_HERE` with your actual token.

---

## Step 3: Start

```bash
# Start all services
docker-compose up -d

# Wait 30 seconds for services to start

# Check logs
docker-compose logs -f truthsnap-bot
```

You should see: `Bot started successfully!`

---

## Step 4: Test

1. Open Telegram
2. Find your bot
3. Send `/start`
4. Upload any photo
5. Wait 20-30 seconds
6. Get result! 🎉

---

## Troubleshooting

### Bot not responding?

```bash
# Check if bot is running
docker-compose ps

# Check logs
docker-compose logs truthsnap-bot

# Restart
docker-compose restart truthsnap-bot
```

### "Connection refused" error?

```bash
# Check if FraudLens API is running
curl http://localhost:8000/api/v1/health

# Restart API
docker-compose restart fraudlens-api
```

### Workers not processing jobs?

```bash
# Check RQ Dashboard
open http://localhost:9181

# Check worker logs
docker-compose logs truthsnap-worker

# Restart workers
docker-compose restart truthsnap-worker
```

---

## Monitoring

- **RQ Jobs**: http://localhost:9181
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)
- **API Health**: http://localhost:8000/api/v1/health

---

## Next Steps

1. ✅ Bot is running
2. 📸 Test with 10 different photos
3. 🔧 Customize messages in `app/bot/handlers/`
4. 💎 Add real Stripe keys for payments
5. 🚀 Deploy to production (Railway, Fly.io, Render)

---

**Questions?** Open an issue or contact support@truthsnap.ai
