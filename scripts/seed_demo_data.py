"""SQLite에 발표용 VOC를 저장하고 분류·우선순위 결과를 출력한다."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import get_engine, init_database
from app.repositories.voc_repository import DuplicateVOCError
from app.schemas.voc import VOCCreate
from app.services.classification_service import ClassificationService
from app.services.priority_service import PriorityResult, PriorityService
from app.services.voc_service import VOCService


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "demo_priority_result.json"
DEMO_AS_OF = datetime(2026, 11, 17, 16, 0, tzinfo=timezone(timedelta(hours=9)))
GAME_NAME = "Project Arena"


@dataclass(frozen=True, slots=True)
class DemoScenario:
    key: str
    recent_count: int
    previous_count: int
    messages: tuple[str, ...]
    platforms: tuple[str, ...]


SCENARIOS = (
    DemoScenario(
        key="SECURITY",
        recent_count=3,
        previous_count=0,
        messages=(
            "계정이 해킹되어 제가 구매한 아이템이 사라졌습니다.",
            "모르는 지역에서 로그인한 기록이 있고 계정이 도용된 것 같습니다.",
            "해킹으로 비밀번호가 변경되어 계정에 접속할 수 없습니다.",
        ),
        platforms=("Windows", "Android", "iOS"),
    ),
    DemoScenario(
        key="CRASH",
        recent_count=10,
        previous_count=2,
        messages=(
            "업데이트 후 전투에 입장하면 게임이 강제 종료됩니다.",
            "보스전 로딩 화면에서 계속 튕기고 강제 종료됩니다.",
            "게임 실행 중 오류가 발생하며 갑자기 강제 종료됩니다.",
        ),
        platforms=("Windows", "Windows", "Steam Deck"),
    ),
    DemoScenario(
        key="PAYMENT",
        recent_count=3,
        previous_count=4,
        messages=(
            "상점에서 같은 상품이 중복 결제되어 두 번 청구됐습니다.",
            "패키지를 한 번 구매했는데 결제가 두 번 처리됐습니다.",
            "중복 결제된 주문을 확인하고 환불해 주세요.",
        ),
        platforms=("Android", "iOS", "Windows"),
    ),
    DemoScenario(
        key="HARASSMENT",
        recent_count=4,
        previous_count=1,
        messages=(
            "채팅에서 욕설하며 계속 따라다니고 괴롭히는 이용자를 신고합니다.",
            "게임 내 욕설과 비매너 행동으로 괴롭힘을 당하고 있습니다.",
            "파티 채팅에서 지속적으로 욕설하는 사용자를 신고합니다.",
        ),
        platforms=("Windows", "Android", "iOS"),
    ),
    DemoScenario(
        key="PERFORMANCE",
        recent_count=2,
        previous_count=3,
        messages=(
            "업데이트 후 렉과 프레임 지연이 심해서 플레이가 어렵습니다.",
            "전투 중 프레임이 떨어지고 입력 지연이 발생합니다.",
            "게임이 너무 느려지고 렉이 계속 발생합니다.",
        ),
        platforms=("Windows", "Steam Deck"),
    ),
    DemoScenario(
        key="SUGGESTION",
        recent_count=8,
        previous_count=0,
        messages=(
            "인벤토리 정렬 기능을 추가해 주셨으면 좋겠습니다.",
            "친구 목록 검색 기능 개선을 건의합니다.",
            "전투 기록을 다시 볼 수 있는 기능을 제안합니다.",
        ),
        platforms=("Windows", "Android", "iOS"),
    ),
)


def build_demo_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    channels = ("website", "phone", "sns")

    for scenario in SCENARIOS:
        periods = (
            ("PREVIOUS", scenario.previous_count, 8),
            ("RECENT", scenario.recent_count, 1),
        )
        sequence = 0
        for period, count, first_day_ago in periods:
            for index in range(count):
                sequence += 1
                day_offset = first_day_ago + index % 6
                received_at = DEMO_AS_OF - timedelta(
                    days=day_offset,
                    hours=index % 5,
                )
                payloads.append(
                    {
                        "external_id": f"DEMO-{scenario.key}-{period}-{index + 1:02d}",
                        "channel": channels[index % len(channels)],
                        "content": scenario.messages[index % len(scenario.messages)],
                        "received_at": received_at.isoformat(),
                        "game_name": GAME_NAME,
                        "platform": scenario.platforms[index % len(scenario.platforms)],
                        "game_version": "1.0.0",
                        "metadata": {
                            "demo": True,
                            "scenario": scenario.key,
                            "sequence": sequence,
                        },
                    }
                )
    return payloads


def _result_to_dict(result: PriorityResult) -> dict[str, Any]:
    group = result.group
    priority = result.priority
    return {
        "priority_rank": priority.priority_rank,
        "priority_grade": priority.priority_grade,
        "priority_score": float(priority.priority_score),
        "issue_group_id": group.id,
        "title": group.title,
        "category": group.category,
        "topic": group.topic,
        "inquiry_count": group.inquiry_count,
        "severity_level": priority.severity_level,
        "severity_score": float(priority.severity_score),
        "recent_7d_count": priority.recent_7d_count,
        "previous_7d_count": priority.previous_7d_count,
        "growth_rate_percent": float(priority.growth_rate_percent),
        "reasons": priority.reasons,
    }


def _print_priorities(results: list[PriorityResult]) -> None:
    print("\n" + "=" * 78)
    print("해결 우선순위 결과")
    print("=" * 78)
    for result in results:
        group = result.group
        priority = result.priority
        print(
            f"{priority.priority_rank:>2}위 [{priority.priority_grade}] "
            f"{group.title} | {float(priority.priority_score):.2f}점"
        )
        print(
            f"    심각도 {priority.severity_level}({float(priority.severity_score):.2f}/5), "
            f"누적 {group.inquiry_count}건, 최근 7일 {priority.recent_7d_count}건, "
            f"직전 7일 {priority.previous_7d_count}건"
        )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("[1/4] SQLite 데이터베이스와 테이블을 확인합니다.")
    init_database()

    payloads = build_demo_payloads()
    created_count = 0
    duplicate_count = 0
    voc_service = VOCService()

    print(f"[2/4] 시연용 VOC {len(payloads)}건을 등록합니다.")
    with Session(get_engine()) as session:
        for payload in payloads:
            try:
                voc_service.create(session, VOCCreate.model_validate(payload))
            except DuplicateVOCError:
                duplicate_count += 1
            else:
                created_count += 1

        print(
            f"      신규 {created_count}건, 이미 존재해 제외 {duplicate_count}건"
        )

        print("[3/4] 미분석 VOC를 분류하고 같은 문제끼리 그룹화합니다.")
        classification = ClassificationService().run_pending(session, limit=5_000)
        print(
            f"      분석 {classification.processed_count}건, "
            f"새 문제 그룹 {classification.created_group_count}개, "
            f"기존 그룹 갱신 {classification.updated_group_count}개"
        )

        print("[4/4] 심각도·문의량·증가 추세로 해결 우선순위를 계산합니다.")
        priority_run = PriorityService().recalculate(session, DEMO_AS_OF)
        demo_results = [
            item
            for item in priority_run.items
            if item.group.title.startswith(f"{GAME_NAME} - ")
        ]

    _print_priorities(demo_results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "as_of": DEMO_AS_OF.isoformat(),
                "registered_count": len(payloads),
                "issue_group_count": len(demo_results),
                "priorities": [_result_to_dict(item) for item in demo_results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n결과 JSON 저장 완료: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
