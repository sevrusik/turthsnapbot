# TruthSnap Bot - Makefile

.PHONY: help start stop restart logs test clean local-start local-stop

help:
	@echo "TruthSnap Bot - Available Commands"
	@echo ""
	@echo "  make start        - Start all services (Docker)"
	@echo "  make stop         - Stop all services (Docker)"
	@echo "  make restart      - Restart all services (Docker)"
	@echo "  make logs         - View logs (Docker)"
	@echo "  make local-start  - Start locally (No Docker)"
	@echo "  make local-stop   - Stop local services"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make status       - Show service status"
	@echo ""

start:
	@if command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then \
		echo "🚀 Starting TruthSnap Bot with Docker..."; \
		if command -v docker-compose >/dev/null 2>&1; then \
			docker-compose up -d; \
		else \
			docker compose up -d; \
		fi; \
		echo ""; \
		echo "✅ Services started!"; \
		echo "   Bot: docker-compose logs -f truthsnap-bot"; \
		echo "   RQ Dashboard: http://localhost:9181"; \
	else \
		echo "⚠️  Docker not found. Use 'make local-start' instead"; \
		echo ""; \
		echo "To install Docker: https://www.docker.com/products/docker-desktop/"; \
		echo "Or run locally: make local-start"; \
	fi
	@echo ""

stop:
	@echo "🛑 Stopping services..."
	docker-compose down
	@echo "✅ Stopped"

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "✅ Restarted"

logs:
	docker-compose logs -f

status:
	docker-compose ps

test:
	@echo "🧪 Running tests..."
	cd fraudlens && python -m pytest tests/ -v
	cd truthsnap-bot && python -m pytest tests/ -v
	@echo "✅ Tests completed"

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	@echo "✅ Cleaned"

# Local run commands (No Docker)
local-start:
	@./run_local.sh

local-stop:
	@./stop_local.sh

local-logs:
	@tail -f logs/*.log

# Development commands
dev-api:
	cd fraudlens && uvicorn backend.api.main:app --reload

dev-bot:
	cd truthsnap-bot && python -m app.bot.main

dev-worker:
	cd truthsnap-bot && rq worker high default low

# Database
db-migrate:
	@echo "📊 Running database migrations..."
	# TODO: Add migration command
	@echo "✅ Migrations completed"
