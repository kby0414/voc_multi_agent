"""DB 연결 없이 검증 가능한 VOC 요청 스키마 테스트."""

from __future__ import annotations

import unittest
from datetime import datetime

from pydantic import ValidationError

from app.schemas.voc import VOCCreate


class VOCCreateSchemaTests(unittest.TestCase):
    def test_timezone_is_required(self) -> None:
        with self.assertRaises(ValidationError):
            VOCCreate(
                channel="website",
                content="업데이트 후 게임이 종료됩니다.",
                received_at=datetime(2026, 11, 17, 12, 0),
            )

    def test_timezone_aware_datetime_is_accepted(self) -> None:
        payload = VOCCreate.model_validate(
            {
                "channel": "sns",
                "content": "중복 결제가 발생했습니다.",
                "received_at": "2026-11-17T12:00:00+09:00",
            }
        )
        self.assertIsNotNone(payload.received_at.utcoffset())


if __name__ == "__main__":
    unittest.main()
