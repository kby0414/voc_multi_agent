"""수집·분류 에이전트의 핵심 규칙 검증."""

from __future__ import annotations

import unittest

from voc_system.agents import AnalystAgent, CollectorAgent
from voc_system.llm import LLMService


class AgentTests(unittest.TestCase):
    def setUp(self) -> None:
        llm = LLMService(mode="rules")
        self.collector = CollectorAgent(llm)
        self.analyst = AnalystAgent(llm)

    def test_sensitive_information_is_masked(self) -> None:
        item = self.collector.run(
            {
                "channel": "sns",
                "message": "연락처는 010-1234-5678이고 메일은 gamer@example.com입니다.",
            }
        )
        self.assertNotIn("010-1234-5678", item.masked_message)
        self.assertNotIn("gamer@example.com", item.masked_message)

    def test_payment_voc_is_classified(self) -> None:
        item = self.collector.run(
            {"channel": "website", "message": "상품 결제가 두 번 됐습니다."}
        )
        result = self.analyst.run(item)
        self.assertEqual(result.category, "결제")
        self.assertEqual(result.topic, "중복 결제")
        self.assertIn("결제 이상", result.feature_tags)

    def test_login_then_crash_is_classified_as_technical_error(self) -> None:
        item = self.collector.run(
            {
                "channel": "website",
                "message": "게임 로그인을 하고 게임 실행을 했는데 게임이 팅겨요",
            }
        )
        result = self.analyst.run(item)
        self.assertEqual(result.category, "기술 오류")
        self.assertEqual(result.topic, "강제 종료")

    def test_agent_a_and_b_use_named_prompt_files(self) -> None:
        self.assertEqual(self.collector.agent_code, "A")
        self.assertEqual(self.analyst.agent_code, "B")
        self.assertEqual(self.collector.prompt_path.name, "agent_a_collector.md")
        self.assertEqual(self.analyst.prompt_path.name, "agent_b_classifier.md")
        self.assertTrue(self.collector.prompt_path.is_file())
        self.assertTrue(self.analyst.prompt_path.is_file())


if __name__ == "__main__":
    unittest.main()
