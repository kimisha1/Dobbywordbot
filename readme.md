# Telegram Formal English Rewriter Bot

A single-file Telegram bot (`bot.py`) that sends user messages to Fireworks AI and replies with a formal, polished English version.

Telegram bot :@Dobbywordbot

## Features
- Formal English rewrite using Fireworks AI (`
Dobby-Unhinged-Llama-3.3-70B`)
- Long polling (no webhook required)
- Global concurrency limit to handle simultaneous requests
- Simple retries with exponential backoff
- Typing indicator and friendly error messages

## Requirements
- Python 3.10+
- Telegram Bot Token
- Fireworks API Key

## Install
```bash
pip install python-telegram-bot==21.6 requests
```

## Configuration
Keys are currently inlined in `bot.py` for simplicity. Replace them with your real values:
- `TELEGRAM_BOT_TOKEN = "<YOUR_TELEGRAM_BOT_TOKEN>"`
- `FIREWORKS_API_KEY = "<YOUR_FIREWORKS_API_KEY>"`

Optional concurrency tuning in `bot.py`:
- `GLOBAL_MAX_CONCURRENT_REQUESTS = 5` (increase/decrease as needed)

Model and endpoint:
- `FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"`
- `FIREWORKS_MODEL = "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new"`

## Run
```bash
python bot.py
```
You should see:
```
Bot is running. Press Ctrl+C to stop.
```

## Usage
- Open your Telegram client
- Start the bot via `/start`
- Send any English text; the bot replies with a formal, refined version

## How it works (high-level)
- The bot listens with long polling using `python-telegram-bot`
- For each text message:
  - Shows typing indicator
  - Enters a global semaphore (limits concurrent API calls)
  - Calls Fireworks AI (with retries) in a background thread
  - Replies with the rewritten text

## Troubleshooting
- Event loop already running (Windows/Python 3.11+):
  - This bot uses a synchronous `main()` with `app.run_polling()` to avoid this. Ensure you run `python bot.py` from a normal shell.
- Unauthorized / invalid token:
  - Double-check `TELEGRAM_BOT_TOKEN` and that the bot is started in BotFather.
- 401/403 from Fireworks:
  - Verify `FIREWORKS_API_KEY` and account/model access.
- Slow responses / rate limiting:
  - Lower `GLOBAL_MAX_CONCURRENT_REQUESTS` or increase it carefully to match your quota and server capacity.

## Notes
- For production, consider moving secrets to environment variables or a secrets manager.
- Add logging and monitoring if running at scale.
- You can swap the system instruction to change rewriting style or language.




