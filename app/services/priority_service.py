"""문제 그룹의 심각도, 문의량과 증가 추세를 종합해 해결 순위를 계산한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.analysis import IssueGroup, IssuePriority
from app.repositories.analysis_repository import AnalysisRepository


CALCULATION_VERSION = "priority-rules-v1"
PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"

# 기능 영향, 피해 규모, 복구 난이도, 시간 민감도, 설명
TOPIC_RUBRICS: dict[str, tuple[float, float, float, float, str]] = {
    "보안 침해": (5.0, 5.0, 4.5, 5.0, "계정 통제권과 자산 피해 가능성"),
    "불법 프로그램": (4.5, 4.5, 3.5, 4.5, "다수 이용자의 공정성 훼손 가능성"),
    "중복 결제": (3.5, 4.5, 3.5, 4.5, "실제 금전 피해 발생"),
    "접속 불가": (5.0, 3.0, 3.0, 4.0, "핵심 서비스 이용 불가"),
    "강제 종료": (4.5, 2.5, 3.0, 3.5, "게임 진행 중단과 데이터 손실 가능성"),
    "이용자 괴롭힘": (3.5, 4.0, 3.0, 4.0, "이용자 안전과 커뮤니티 피해"),
    "환불 요청": (2.5, 3.5, 3.0, 3.5, "금전 관련 처리 필요"),
    "로그인·인증": (4.0, 2.5, 2.5, 3.5, "계정 이용 제한"),
    "성능 저하": (3.5, 2.0, 2.5, 2.5, "플레이 품질 저하"),
    "보상 누락": (2.5, 3.0, 3.0, 3.0, "게임 자산과 운영 신뢰 피해"),
    "기능 개선 제안": (1.5, 1.0, 1.0, 1.0, "즉시 장애가 아닌 개선 요청"),
}

CATEGORY_RUBRICS: dict[str, tuple[float, float, float, float, str]] = {
    "계정": (4.0, 3.5, 3.0, 4.0, "계정 이용과 보안 관련 문제"),
    "결제": (3.0, 4.0, 3.0, 4.0, "금전 관련 문제"),
    "기술 오류": (4.0, 2.5, 3.0, 3.0, "서비스 안정성 문제"),
    "게임 운영": (2.5, 3.0, 2.5, 2.5, "운영 품질과 공정성 문제"),
    "커뮤니티": (3.0, 3.5, 2.5, 3.5, "커뮤니티 안전 문제"),
    "제안": (1.5, 1.0, 1.0, 1.0, "개선 요청"),
    "기타": (2.0, 1.5, 1.5, 1.5, "일반 문의"),
}

# 위험 신호가 있으면 각 심각도 요소에 적용할 최소 점수
RISK_FLOORS: dict[str, tuple[float, float, float, float]] = {
    "안전 위험": (5.0, 5.0, 5.0, 5.0),
    "개인정보": (4.0, 5.0, 4.5, 5.0),
    "계정 보안": (4.5, 5.0, 4.5, 5.0),
    "미성년자 결제": (3.5, 4.5, 3.5, 4.5),
    "법적 분쟁": (3.0, 4.5, 4.0, 4.5),
}


@dataclass(frozen=True, slots=True)
class SeverityAssessment:
    impact_score: float
    damage_score: float
    recoverability_score: float
    time_sensitivity_score: float
    severity_score: float
    severity_level: str
    reasons: list[str]


@dataclass(frozen=True, slots=True)
class TrendAssessment:
    recent_7d_count: int
    previous_7d_count: int
    growth_rate_percent: float
    trend_score: float


@dataclass(slots=True)
class PriorityDraft:
    group: IssueGroup
    severity: SeverityAssessment
    volume_score: float
    trend: TrendAssessment
    priority_score: float
    priority_grade: str
    reasons: list[str]


@dataclass(slots=True)
class PriorityResult:
    group: IssueGroup
    priority: IssuePriority


@dataclass(slots=True)
class PriorityRun:
    as_of_utc: datetime
    items: list[PriorityResult]


def calculate_severity(
    topic: str, category: str, risk_flags: set[str] | None = None
) -> SeverityAssessment:
    rubric = TOPIC_RUBRICS.get(
        topic,
        CATEGORY_RUBRICS.get(category, CATEGORY_RUBRICS["기타"]),
    )
    impact, damage, recoverability, time_sensitivity, rationale = rubric
    flags = risk_flags or set()

    for flag in flags:
        floor = RISK_FLOORS.get(flag)
        if floor:
            impact = max(impact, floor[0])
            damage = max(damage, floor[1])
            recoverability = max(recoverability, floor[2])
            time_sensitivity = max(time_sensitivity, floor[3])

    score = round(
        impact * 0.35
        + damage * 0.30
        + recoverability * 0.20
        + time_sensitivity * 0.15,
        2,
    )
    if flags & {"안전 위험", "개인정보", "계정 보안"}:
        score = max(score, 4.5)

    level = (
        "긴급"
        if score >= 4.5
        else "높음"
        if score >= 3.5
        else "보통"
        if score >= 2.5
        else "낮음"
    )
    reasons = [f"{rationale}: 심각도 {score:.2f}/5 ({level})"]
    if flags:
        reasons.append(f"위험 신호 반영: {', '.join(sorted(flags))}")
    return SeverityAssessment(
        impact_score=impact,
        damage_score=damage,
        recoverability_score=recoverability,
        time_sensitivity_score=time_sensitivity,
        severity_score=score,
        severity_level=level,
        reasons=reasons,
    )


def calculate_volume_score(inquiry_count: int) -> float:
    if inquiry_count >= 20:
        return 5.0
    if inquiry_count >= 10:
        return 4.0
    if inquiry_count >= 5:
        return 3.0
    if inquiry_count >= 2:
        return 2.0
    return 1.0


def calculate_trend(received_at_values: list[datetime], as_of_utc: datetime) -> TrendAssessment:
    recent_start = as_of_utc - timedelta(days=7)
    previous_start = as_of_utc - timedelta(days=14)
    recent = sum(recent_start <= value <= as_of_utc for value in received_at_values)
    previous = sum(previous_start <= value < recent_start for value in received_at_values)

    if previous == 0:
        growth_rate = 100.0 if recent > 0 else 0.0
        if recent >= 10:
            trend_score = 5.0
        elif recent >= 5:
            trend_score = 4.5
        elif recent >= 2:
            trend_score = 4.0
        elif recent == 1:
            trend_score = 3.0
        else:
            trend_score = 1.0
    else:
        growth_rate = round((recent - previous) / previous * 100, 2)
        if growth_rate <= 0:
            trend_score = 1.0
        elif growth_rate <= 25:
            trend_score = 2.0
        elif growth_rate <= 100:
            trend_score = 3.0
        elif growth_rate <= 200:
            trend_score = 4.0
        else:
            trend_score = 5.0

    return TrendAssessment(
        recent_7d_count=recent,
        previous_7d_count=previous,
        growth_rate_percent=growth_rate,
        trend_score=trend_score,
    )


def calculate_priority_score(
    severity_score: float,
    severity_level: str,
    volume_score: float,
    trend_score: float,
) -> tuple[float, str]:
    score = round(
        (severity_score * 0.60 + volume_score * 0.25 + trend_score * 0.15) * 20,
        2,
    )
    if severity_level == "긴급":
        score = max(score, 90.0)
    elif severity_level == "높음":
        score = max(score, 70.0)
    if score >= 90:
        grade = "P0"
    elif score >= 70:
        grade = "P1"
    elif score >= 50:
        grade = "P2"
    else:
        grade = "P3"
    return score, grade


class SeverityAgent:
    """Agent C: 문제 그룹의 피해 수준을 고정 기준으로 평가한다."""

    agent_code = "C"
    prompt_path = PROMPT_DIR / "agent_c_severity.md"

    def run(
        self,
        topic: str,
        category: str,
        risk_flags: set[str] | None = None,
    ) -> SeverityAssessment:
        return calculate_severity(topic, category, risk_flags)


class PriorityAgent:
    """Agent D: 심각도·문의량·추세를 종합해 등급을 결정한다."""

    agent_code = "D"
    prompt_path = PROMPT_DIR / "agent_d_priority.md"

    def run(
        self,
        severity_score: float,
        severity_level: str,
        volume_score: float,
        trend_score: float,
    ) -> tuple[float, str]:
        return calculate_priority_score(
            severity_score,
            severity_level,
            volume_score,
            trend_score,
        )


class PriorityService:
    def __init__(
        self,
        repository: AnalysisRepository | None = None,
        severity_agent: SeverityAgent | None = None,
        priority_agent: PriorityAgent | None = None,
    ) -> None:
        self.repository = repository or AnalysisRepository()
        self.severity_agent = severity_agent or SeverityAgent()
        self.priority_agent = priority_agent or PriorityAgent()

    def recalculate(
        self, session: Session, as_of: datetime | None = None
    ) -> PriorityRun:
        as_of_utc = self.normalize_as_of(as_of)
        drafts: list[PriorityDraft] = []

        for group in self.repository.list_groups(session):
            evidence = self.repository.list_group_evidence(session, group.id)
            received_at_values = [value for value, _ in evidence]
            risk_flags = {flag for _, flags in evidence for flag in flags}
            severity = self.severity_agent.run(group.topic, group.category, risk_flags)
            volume_score = calculate_volume_score(group.inquiry_count)
            trend = calculate_trend(received_at_values, as_of_utc)
            priority_score, priority_grade = self.priority_agent.run(
                severity.severity_score,
                severity.severity_level,
                volume_score,
                trend.trend_score,
            )
            reasons = severity.reasons + [
                f"누적 문의 {group.inquiry_count}건: 문의량 점수 {volume_score:.1f}/5",
                (
                    f"최근 7일 {trend.recent_7d_count}건, 직전 7일 "
                    f"{trend.previous_7d_count}건: 추세 점수 {trend.trend_score:.1f}/5"
                ),
            ]
            drafts.append(
                PriorityDraft(
                    group=group,
                    severity=severity,
                    volume_score=volume_score,
                    trend=trend,
                    priority_score=priority_score,
                    priority_grade=priority_grade,
                    reasons=reasons,
                )
            )

        drafts.sort(
            key=lambda item: (
                -item.priority_score,
                -item.severity.severity_score,
                -item.group.inquiry_count,
                item.group.id,
            )
        )

        results: list[PriorityResult] = []
        for rank, draft in enumerate(drafts, start=1):
            priority = self.repository.get_priority(session, draft.group.id)
            if priority is None:
                priority = IssuePriority(issue_group_id=draft.group.id)
                self.repository.add_priority(session, priority)
            self._apply(priority, draft, rank, as_of_utc)
            results.append(PriorityResult(group=draft.group, priority=priority))

        session.commit()
        for result in results:
            session.refresh(result.priority)
        return PriorityRun(as_of_utc=as_of_utc, items=results)

    def list_current(self, session: Session) -> list[PriorityResult]:
        return [
            PriorityResult(group=group, priority=priority)
            for priority, group in self.repository.list_priorities(session)
        ]

    @staticmethod
    def normalize_as_of(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc).replace(tzinfo=None)
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of에는 +09:00 또는 Z 같은 시간대 정보가 필요합니다.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _apply(
        priority: IssuePriority,
        draft: PriorityDraft,
        rank: int,
        as_of_utc: datetime,
    ) -> None:
        severity = draft.severity
        trend = draft.trend
        priority.impact_score = Decimal(str(severity.impact_score))
        priority.damage_score = Decimal(str(severity.damage_score))
        priority.recoverability_score = Decimal(str(severity.recoverability_score))
        priority.time_sensitivity_score = Decimal(str(severity.time_sensitivity_score))
        priority.severity_score = Decimal(str(severity.severity_score))
        priority.severity_level = severity.severity_level
        priority.volume_score = Decimal(str(draft.volume_score))
        priority.trend_score = Decimal(str(trend.trend_score))
        priority.recent_7d_count = trend.recent_7d_count
        priority.previous_7d_count = trend.previous_7d_count
        priority.growth_rate_percent = Decimal(str(trend.growth_rate_percent))
        priority.priority_score = Decimal(str(draft.priority_score))
        priority.priority_grade = draft.priority_grade
        priority.priority_rank = rank
        priority.reasons = draft.reasons
        priority.calculation_version = CALCULATION_VERSION
        priority.as_of_utc = as_of_utc
