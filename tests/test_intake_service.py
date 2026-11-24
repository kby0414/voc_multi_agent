"""고객 접수 서비스가 내부 처리 단계를 서버에서 연결하는지 검증."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.schemas.voc import CustomerVOCIntake
from app.services.intake_service import IntakeService


class IntakeServiceTests(unittest.TestCase):
    def test_customer_payload_is_stored_as_website_and_analyzed(self) -> None:
        stored_voc = SimpleNamespace(id=41, external_id="VOC-TEST41")
        voc_service = Mock()
        voc_service.create.return_value = stored_voc
        classification_service = Mock()
        classification_service.run_voc.return_value = SimpleNamespace(processed_count=1)
        priority_service = Mock()
        service = IntakeService(voc_service, classification_service, priority_service)
        session = Mock()

        result = service.receive_customer_voc(
            session,
            CustomerVOCIntake(
                game_name="Project Arena",
                platform="Windows",
                content="게임이 실행 중에 팅겨요",
            ),
        )

        stored_payload = voc_service.create.call_args.args[1]
        self.assertEqual(stored_payload.channel, "웹사이트")
        self.assertEqual(stored_payload.game_name, "Project Arena")
        self.assertEqual(result.processing_status, "분석 완료")
        classification_service.run_voc.assert_called_once_with(session, 41)
        priority_service.recalculate.assert_called_once_with(session)


if __name__ == "__main__":
    unittest.main()
