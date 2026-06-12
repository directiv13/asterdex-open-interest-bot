from __future__ import annotations

from telegram import Bot
from telegram.error import TelegramError

from config.settings import settings
from src.utilities.logger import logger


class TelegramNotifier:
    def __init__(self, token: str | None = None) -> None:
        self.bot = Bot(token=token or settings.TELEGRAM_BOT_TOKEN)

    async def send_channel_message(self, text: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHANNEL_ID:
            logger.warning("Telegram channel not configured; skipping alert")
            return
        try:
            await self.bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, message_thread_id=settings.TELEGRAM_CHANNEL_THREAD_ID, text=text, parse_mode="HTML")
            logger.info("Telegram alert sent to {}", settings.TELEGRAM_CHANNEL_ID)
        except TelegramError as exc:
            logger.exception("Telegram send failed: {}", exc)

    async def is_admin(self, user_id: int) -> bool:
        return user_id in settings.TELEGRAM_ALLOWED_USERS
