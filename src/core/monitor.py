from __future__ import annotations

from datetime import datetime, timezone

from src.utilities.logger import logger
from src.utilities.redis import RedisOIHistory
from src.utilities.telegram import TelegramNotifier


class SplashMonitor:
    def __init__(self, redis_client: RedisOIHistory, telegram_client: TelegramNotifier) -> None:
        self.redis = redis_client
        self.telegram = telegram_client

    @staticmethod
    def format_time(seconds: int) -> str:
        minutes, secs = divmod(seconds, 60)
        if minutes:
            return f"{minutes} min {secs} secs"
        return f"{secs} secs"

    async def process_open_interest(self, payload: dict) -> bool:
        symbol = str(payload.get("symbol", "")).strip().upper()
        oi = float(payload.get("openInterest", 0) or 0)
        timestamp_ms = int(payload.get("time", 0) or 0)
        current_ts = timestamp_ms // 1000 if timestamp_ms > 1_000_000_000_000 else int(timestamp_ms)

        if not symbol or oi <= 0:
            logger.warning("Skipping invalid OI payload for {}", symbol)
            return False

        await self.redis.add_sample(symbol, oi, current_ts)
        await self.redis.cleanup_old(symbol, current_ts)

        match = await self.redis.find_oldest_match(symbol, oi, current_ts)
        if not match:
            return False

        old_ts = int(match["old_timestamp"])
        old_oi = float(match["old_oi"])
        increase_pct = float(match["increase_pct"])
        elapsed_seconds = max(0, current_ts - old_ts)

        now = datetime.now(timezone.utc)
        timestamp_text = now.strftime("%Y-%m-%d %H:%M:%S")

        text = (
            "🚀 <b>OI SPLASH DETECTED</b>\n\n"
            f"    Symbol: <code>{symbol}</code>\n"
            f"    OI Increase: +{increase_pct:.2f}%\n"
            f"    Time: {self.format_time(elapsed_seconds)}\n"
            f"    OI Change: {int(old_oi):,} → {int(oi):,}\n\n"
            f"    Timestamp: {timestamp_text}"
        )

        await self.telegram.send_channel_message(text)
        await self.redis.clear_symbol(symbol)
        logger.success("Detected splash for {} with +{:.2f}% in {}", symbol, increase_pct, self.format_time(elapsed_seconds))
        return True
