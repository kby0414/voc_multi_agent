"""발표용 SQLite 데이터 생성 규칙 검증."""

from __future__ import annotations

import unittest

from scripts.seed_demo_data import build_demo_payloads


class DemoSeedTests(unittest.TestCase):
    def test_demo_payload_count_and_ids_are_stable(self) -> None:
        payloads = build_demo_payloads()
        external_ids = {item["external_id"] for item in payloads}
        self.assertEqual(len(payloads), 40)
        self.assertEqual(len(external_ids), 40)

    def test_demo_payloads_have_timezone_and_scenarios(self) -> None:
        payloads = build_demo_payloads()
        self.assertTrue(all("+09:00" in item["received_at"] for item in payloads))
        scenarios = {item["metadata"]["scenario"] for item in payloads}
        self.assertEqual(
            scenarios,
            {"SECURITY", "CRASH", "PAYMENT", "HARASSMENT", "PERFORMANCE", "SUGGESTION"},
        )


if __name__ == "__main__":
    unittest.main()
