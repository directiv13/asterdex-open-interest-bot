from __future__ import annotations

import asyncio
import sys

from config.settings import settings
from src.core.monitor import SplashMonitor
from src.utilities.asterdex import AsterDEXClient
from src.utilities.logger import logger
from src.utilities.redis import RedisOIHistory
from src.utilities.telegram import TelegramNotifier


async def run_once() -> None:
    redis_client = RedisOIHistory()
    telegram_client = TelegramNotifier()
    monitor = SplashMonitor(redis_client, telegram_client)
    asterdex = AsterDEXClient()

    try:
        tickers = await asterdex.get_all_tickers()
        symbols = [str(item.get("symbol", "")).strip().upper() for item in tickers if str(item.get("symbol")).endswith("USDT")]
        if not symbols:
            logger.warning("No tickers returned by AsterDEX; nothing to monitor")
            return

        results = await asterdex.get_open_interest_for_symbols(symbols)
        for payload in results:
            try:
                await monitor.process_open_interest(payload)
            except Exception as exc:
                logger.exception("Failed to process OI payload for {}: {}", payload.get("symbol"), exc)
    finally:
        await redis_client.close()


async def main() -> None:
    logger.info("Starting AsterDEX OI bot with polling interval {} seconds", settings.POLL_INTERVAL_SECONDS)
    while True:
        try:
            await run_once()
        except Exception as exc:
            logger.exception("Main cycle failed: {}", exc)
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        asyncio.run(run_once())
    else:
        asyncio.run(main())
