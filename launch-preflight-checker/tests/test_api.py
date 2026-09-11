import unittest
from unittest.mock import AsyncMock, patch

from app.checker import Check, Report
from app.main import check


class ApiVerdictTest(unittest.IsolatedAsyncioTestCase):
    @patch("app.main.inspect_url", new_callable=AsyncMock)
    async def test_telegram_wrapper_cannot_be_ready(self, inspect_mock):
        inspect_mock.return_value = Report(
            input_url="https://t.me/test_bot/aboutme?startapp=a_123",
            final_url="https://t.me/test_bot/aboutme?startapp=a_123",
            checked_at="2026-09-11T00:00:00+00:00",
            score=100,
            verdict="READY",
            summary={"pass": 8, "warn": 0, "fail": 0, "manual": 1},
            checks=[
                Check(
                    key="telegram_wrapper",
                    title="Telegram Mini App wrapper",
                    status="manual",
                    detail="wrapper only",
                    evidence=[],
                )
            ],
            discovered_links=0,
            checked_links=0,
        )

        result = await check("https://t.me/test_bot/aboutme?startapp=a_123", max_links=20)
        self.assertEqual(result["verdict"], "ATTENTION")

    @patch("app.main.inspect_url", new_callable=AsyncMock)
    async def test_regular_ready_report_stays_ready(self, inspect_mock):
        inspect_mock.return_value = Report(
            input_url="https://example.com",
            final_url="https://example.com",
            checked_at="2026-09-11T00:00:00+00:00",
            score=100,
            verdict="READY",
            summary={"pass": 8, "warn": 0, "fail": 0, "manual": 0},
            checks=[],
            discovered_links=0,
            checked_links=0,
        )

        result = await check("https://example.com", max_links=20)
        self.assertEqual(result["verdict"], "READY")


if __name__ == "__main__":
    unittest.main()
