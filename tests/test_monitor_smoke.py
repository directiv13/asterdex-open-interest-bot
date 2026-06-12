import unittest

from src.core.monitor import SplashMonitor


class FakeRedis:
    def __init__(self) -> None:
        self.history = {}
        self.cleared = []

    async def add_sample(self, symbol, oi, timestamp):
        self.history.setdefault(symbol, []).append((timestamp, oi))

    async def cleanup_old(self, symbol, now_ts):
        return None

    async def find_oldest_match(self, symbol, current_oi, current_ts):
        candidates = []
        for old_ts, old_oi in self.history.get(symbol, []):
            ratio = current_oi / old_oi if old_oi else 0.0
            if ratio >= 1.05:
                candidates.append((old_ts, old_oi, ratio))
        if not candidates:
            return None
        old_ts, old_oi, ratio = min(candidates, key=lambda item: item[0])
        return {
            "symbol": symbol,
            "old_timestamp": old_ts,
            "old_oi": old_oi,
            "current_oi": current_oi,
            "current_timestamp": current_ts,
            "ratio": ratio,
            "increase_pct": (ratio - 1.0) * 100.0,
        }

    async def clear_symbol(self, symbol):
        self.cleared.append(symbol)
        self.history.pop(symbol, None)


class FakeTelegram:
    def __init__(self) -> None:
        self.messages = []

    async def send_channel_message(self, text):
        self.messages.append(text)


class SplashMonitorSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def test_process_open_interest_detects_splash_and_clears_history(self) -> None:
        redis_client = FakeRedis()
        telegram_client = FakeTelegram()
        monitor = SplashMonitor(redis_client, telegram_client)

        await redis_client.add_sample("BTCUSDT", 1000.0, 1_700_000_000)
        await monitor.process_open_interest({"symbol": "BTCUSDT", "openInterest": "1100", "time": 1_700_000_120_000})

        self.assertEqual(redis_client.cleared, ["BTCUSDT"])
        self.assertTrue(any("OI SPLASH DETECTED" in message for message in telegram_client.messages))
        self.assertTrue(any("BTCUSDT" in message for message in telegram_client.messages))
        self.assertTrue(any("+10.00%" in message for message in telegram_client.messages))


if __name__ == "__main__":
    unittest.main()
