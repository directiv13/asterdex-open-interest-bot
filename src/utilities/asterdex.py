from __future__ import annotations

import asyncio
from typing import Any

import httpx

from config.settings import settings
from src.utilities.logger import logger


class AsterDEXClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ASTERDEX_BASE_URL).rstrip("/")

    async def get_all_tickers(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/premiumIndex")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("Unexpected payload from /fapi/v1/premiumIndex")
            logger.debug("Fetched {} tickers", len(payload))
            return payload

    async def get_open_interest(self, symbol: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/fapi/v1/openInterest", params={"symbol": symbol})
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Unexpected payload from /fapi/v1/openInterest")
            logger.debug("Fetched OI for {}", symbol)
            return payload

    async def get_open_interest_for_symbols(self, symbols: list[str]) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(10)

        async def fetch_one(symbol: str) -> dict[str, Any]:
            async with semaphore:
                return await self.get_open_interest(symbol)

        results = await asyncio.gather(
            *(fetch_one(symbol) for symbol in symbols),
            return_exceptions=True
        )
        return [r for r in results if not isinstance(r, BaseException)]
