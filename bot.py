import json
import asyncio
from typing import Optional
import time

import requests
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


TELEGRAM_BOT_TOKEN = "8355863786:AAHwdCwfyYSkq-E41VDxY2sRNhSyc6MwV4I"
FIREWORKS_API_KEY = "fw_3ZkbWdZZRJTxUueSqoFckNJ9"
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
FIREWORKS_MODEL = "accounts/fireworks/models/deepseek-v3p1"
GLOBAL_MAX_CONCURRENT_REQUESTS = 5
_ai_call_semaphore = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT_REQUESTS)


def call_fireworks_formalize_english(user_text: str) -> str:
	"""Call Fireworks AI to rewrite text into formal English and return the result or raise."""
	if not FIREWORKS_API_KEY or "<FIREWORKS_API_KEY>" in FIREWORKS_API_KEY:
		raise RuntimeError("FIREWORKS_API_KEY is not set in code")

	# System instruction to formalize English text
	system_instruction = (
		"You are an expert English editor. Rewrite the user's text in a formal, "
		"clear, respectful tone. Preserve the meaning; improve grammar, spelling, "
		"and punctuation. Do not add explanations or extra content. Output only the "
		"final rewritten text."
	)

	payload = {
		"model": FIREWORKS_MODEL,
		"max_tokens": 1024,
		"top_p": 1,
		"top_k": 40,
		"presence_penalty": 0,
		"frequency_penalty": 0,
		"temperature": 0.4,
		"messages": [
			{"role": "system", "content": system_instruction},
			{"role": "user", "content": user_text},
		],
	}

	headers = {
		"Accept": "application/json",
		"Content-Type": "application/json",
		"Authorization": f"Bearer {FIREWORKS_API_KEY}",
	}

	response = requests.post(FIREWORKS_URL, headers=headers, data=json.dumps(payload), timeout=60)
	if response.status_code != 200:
		raise RuntimeError(f"Fireworks API error: {response.status_code} {response.text}")

	data = response.json()
	choices = data.get("choices") or []
	if not choices:
		raise RuntimeError("Fireworks API returned no choices")

	message = choices[0].get("message") or {}
	content = message.get("content")
	if not content:
		raise RuntimeError("Fireworks API returned empty content")
	return content.strip()


def _call_fireworks_with_retry(user_text: str, attempts: int = 3, base_delay_seconds: float = 0.75) -> str:
	"""Call the Fireworks API with simple exponential backoff retries."""
	last_error: Optional[Exception] = None
	for attempt_index in range(attempts):
		try:
			return call_fireworks_formalize_english(user_text)
		except Exception as exc:  # noqa: BLE001 keep broad here to surface text to user if all attempts fail
			last_error = exc
			if attempt_index < attempts - 1:
				time.sleep(base_delay_seconds * (2 ** attempt_index))
				continue
			raise last_error


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Handle /start command."""
	await context.bot.send_message(
		chat_id=update.effective_chat.id,
		text=(
			"Hi!\n"
			"Please send your text and I will return a formal, edited version."
		),
	)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Handle user text messages: send to Fireworks and reply with the formal version."""
	user_text = (update.message.text or "").strip()
	if not user_text:
		return

	# Show typing indicator early
	await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
	wait_msg = await context.bot.send_message(
		chat_id=update.effective_chat.id,
		text="Working on the formal rewrite...",
	)
	try:
		# Limit concurrent API calls globally
		async with _ai_call_semaphore:
			# Run blocking request in a thread to avoid blocking the event loop
			formal_text = await asyncio.to_thread(_call_fireworks_with_retry, user_text)
			await context.bot.send_message(
				chat_id=update.effective_chat.id,
				text=formal_text,
			)
	except Exception as exc:
		await context.bot.send_message(
			chat_id=update.effective_chat.id,
			text=f"Sorry, I couldn't process your request. Error: {exc}",
		)
	finally:
		# Try to delete the waiting message quietly
		try:
			await wait_msg.delete()
		except Exception:
			pass


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await context.bot.send_message(
		chat_id=update.effective_chat.id,
		text=(
			"Just send your text to receive its formal version.\n"
			"Available commands: /start , /help"
		),
	)


def validate_config() -> Optional[str]:
	missing = []
	if not TELEGRAM_BOT_TOKEN or "<TELEGRAM_BOT_TOKEN>" in TELEGRAM_BOT_TOKEN:
		missing.append("TELEGRAM_BOT_TOKEN")
	if not FIREWORKS_API_KEY or "<FIREWORKS_API_KEY>" in FIREWORKS_API_KEY:
		missing.append("FIREWORKS_API_KEY")
	if missing:
		return "Missing required keys in code: " + ", ".join(missing)
	return None


def main() -> None:
	err = validate_config()
	if err:
		raise SystemExit(err)

	app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("help", help_cmd))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

	print("Bot is running. Press Ctrl+C to stop.")
	app.run_polling()


if __name__ == "__main__":
	try:
		main()
	except (KeyboardInterrupt, SystemExit):
		pass
