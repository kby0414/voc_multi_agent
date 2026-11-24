"""심각도와 우선순위 계산 기준 검증."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from app.services.priority_service import (
    PriorityAgent,
    SeverityAgent,
    calculate_priority_score,
    calculate_severity,
    calculate_trend,
    calculate_volume_score,
)


class PriorityServiceTests(unittest.TestCase):
    def test_account_security_risk_is_emergency(self) -> None:
        result = calculate_severity("보안 침해", "계정", {"계정 보안"})
        self.assertEqual(result.severity_level, "긴급")
        self.assertGreaterEqual(result.severity_score, 4.5)

    def test_feature_request_has_low_severity(self) -> None:
        result = calculate_severity("기능 개선 제안", "제안")
        self.assertEqual(result.severity_level, "낮음")

    def test_volume_score_uses_fixed_intervals(self) -> None:
        self.assertEqual(calculate_volume_score(1), 1.0)
        self.assertEqual(calculate_volume_score(7), 3.0)
        self.assertEqual(calculate_volume_score(20), 5.0)

    def test_recent_increase_has_higher_trend_score(self) -> None:
        as_of = datetime(2026, 11, 17, 6, 0, 0)
        timestamps = [as_of - timedelta(days=2), as_of - timedelta(days=3)]
        result = calculate_trend(timestamps, as_of)
        self.assertEqual(result.recent_7d_count, 2)
        self.assertEqual(result.previous_7d_count, 0)
        self.assertEqual(result.trend_score, 4.0)

    def test_emergency_priority_has_p0_floor(self) -> None:
        score, grade = calculate_priority_score(4.5, "긴급", 1.0, 1.0)
        self.assertEqual(score, 90.0)
        self.assertEqual(grade, "P0")

    def test_agent_c_and_d_use_named_prompt_files(self) -> None:
        severity_agent = SeverityAgent()
        priority_agent = PriorityAgent()
        self.assertEqual(severity_agent.agent_code, "C")
        self.assertEqual(priority_agent.agent_code, "D")
        self.assertEqual(severity_agent.prompt_path.name, "agent_c_severity.md")
        self.assertEqual(priority_agent.prompt_path.name, "agent_d_priority.md")
        self.assertTrue(severity_agent.prompt_path.is_file())
        self.assertTrue(priority_agent.prompt_path.is_file())


if __name__ == "__main__":
    unittest.main()
