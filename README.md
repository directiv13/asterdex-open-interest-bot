# AsterDEX OI Telegram Bot

A production-ready async Python bot that monitors AsterDEX open interest (OI), detects a 5%+ splash event within a 60-minute window, and sends an alert to a Telegram channel.

## Features
- Async polling of AsterDEX tickers and OI data
- Redis-backed OI history using Sorted Sets (`oi:history:{symbol}`)
- Splash detection for OI increases of at least 5%
- Telegram channel notifications with the requested alert format
- Docker support and a GitHub Actions deployment workflow for a Linux VPS

## Requirements
- Python 3.12+
- Redis (local or Docker)
- Telegram Bot token from @BotFather
- A Telegram channel ID or username for alerts

## Environment configuration
Create a local `.env` file from the example template:

```bash
cp .env.example .env
```

Set the required values in `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:YOUR_BOT_TOKEN
TELEGRAM_ALLOWED_USERS=123456789
TELEGRAM_CHANNEL_ID=@your_channel
REDIS_URL=redis://localhost:6379/0
ASTERDEX_BASE_URL=https://fapi.asterdex.com
POLL_INTERVAL_SECONDS=60
HISTORY_TTL_SECONDS=3600
```

> Do not commit `.env` to source control.

## Local development setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
3. Start Redis locally (optional if you use Docker instead):
   ```bash
   redis-server
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

For a one-time smoke run:

```bash
python main.py --once
```

## Running with Docker
This repository includes a Docker Compose setup with Redis persistence.

1. Build and start the services:
   ```bash
   docker compose up --build -d
   ```
2. View logs:
   ```bash
   docker compose logs -f bot
   ```
3. Stop the services:
   ```bash
   docker compose down
   ```

The Redis data volume is defined as `redis-data` in `docker-compose.yml`.

## CI/CD deployment to a Linux VPS
The deployment workflow is defined in `.github/workflows/deploy.yml`.

### Required GitHub repository secrets
Set these secrets in your GitHub repository settings:
- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`

### How the workflow works
- On every push to `main`, GitHub Actions runs the deploy job.
- It connects to your Linux VPS over SSH.
- It pulls the latest code and runs:
  ```bash
  docker compose up --build -d
  ```

### Suggested server-side setup
On your VPS, create the deployment directory and clone the repository:

```bash
mkdir -p /opt/aster-oi-bot
cd /opt/aster-oi-bot
git clone <your-repo-url> .
```

Then make sure Docker and Docker Compose are installed on the VPS.

## Project structure
- `main.py` – main async loop and entry point
- `config/settings.py` – environment-based configuration
- `src/utilities/asterdex.py` – AsterDEX HTTP client
- `src/utilities/redis.py` – Redis Sorted Set history wrapper
- `src/utilities/telegram.py` – Telegram channel notification helper
- `src/core/monitor.py` – splash detection and alert formatting
- `Dockerfile` – container image for the bot
- `docker-compose.yml` – bot + Redis stack
- `.github/workflows/deploy.yml` – CI/CD deployment pipeline

## Notes
- The bot uses asynchronous I/O throughout.
- The splash logic looks for the oldest data point in the last 60 minutes where the current OI is at least 5% higher than the historical point.
- Once a splash alert is sent, the symbol history is cleared to avoid repeated spam.
