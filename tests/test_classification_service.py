"""분류·그룹화 서비스의 결정적 동작 검증."""

from __future__ import annotations

import unittest

from app.services.classification_service import build_group_key


class ClassificationServiceTests(unittest.TestCase):
    def test_same_problem_has_same_group_key(self) -> None:
        first = build_group_key("Project Arena", "기술 오류", "강제 종료")
        second = build_group_key(" project arena ", "기술 오류", "강제 종료")
        self.assertEqual(first, second)

    def test_different_topic_has_different_group_key(self) -> None:
        crash = build_group_key("Project Arena", "기술 오류", "강제 종료")
        lag = build_group_key("Project Arena", "기술 오류", "성능 저하")
        self.assertNotEqual(crash, lag)


if __name__ == "__main__":
    unittest.main()
