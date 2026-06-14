from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from config.settings import settings
from src.utilities.logger import logger


class RedisOIHistory:
    def __init__(self, url: str | None = None) -> None:
        self.client = redis.from_url(url or settings.REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        await self.client.aclose()

    def key(self, symbol: str) -> str:
        return f"oi:history:{symbol}"

    async def add_sample(self, symbol: str, oi: float, price: float, timestamp: int) -> None:
        entry = json.dumps({"oi": oi, "price": price}, separators=(",", ":"))
        await self.client.zadd(self.key(symbol), {entry: timestamp})
        await self.client.expire(self.key(symbol), settings.HISTORY_TTL_SECONDS)

    async def cleanup_old(self, symbol: str, now_ts: int) -> None:
        cutoff = now_ts - (settings.HISTORY_TTL_SECONDS + 60)
        removed = await self.client.zremrangebyscore(self.key(symbol), 0, cutoff)
        if removed:
            logger.debug("Removed {} old OI points for {}", removed, symbol)

    async def fetch_history(self, symbol: str, start_ts: int, end_ts: int) -> list[tuple[int, float, float]]:
        raw = await self.client.zrangebyscore(self.key(symbol), min=start_ts, max=end_ts, withscores=True)
        history: list[tuple[int, float, float]] = []
        for value, score in raw:
            raw_value = value if isinstance(value, (str, bytes, bytearray)) else str(value)
            data = json.loads(raw_value)
            history.append((int(score), float(data.get("oi", 0.0)), float(data.get("price", 0.0))))
        return history

    async def find_oldest_match(self, symbol: str, current_oi: float, current_price: float, current_ts: int, threshold: float = 1.15, window_seconds: int = 3600) -> dict[str, Any] | None:
        history = await self.fetch_history(symbol, current_ts - window_seconds, current_ts - 1)
        for old_ts, old_oi, old_price in history:
            ratio = current_oi / old_oi if old_oi else 0.0
            if ratio >= threshold:
                price_ratio = current_price / old_price if old_price else 0.0
                return {
                    "symbol": symbol,
                    "old_timestamp": old_ts,
                    "old_oi": old_oi,
                    "old_price": old_price,
                    "current_oi": current_oi,
                    "current_price": current_price,
                    "current_timestamp": current_ts,
                    "ratio": ratio,
                    "increase_pct": (ratio - 1.0) * 100.0,
                    "price_change_pct": (price_ratio - 1.0) * 100.0,
                }
        return None

    async def clear_symbol(self, symbol: str) -> None:
        await self.client.delete(self.key(symbol))
