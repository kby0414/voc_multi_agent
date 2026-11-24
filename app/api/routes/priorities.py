"""문제 그룹 해결 우선순위 계산과 조회 API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import IssuePriorityListResponse, IssuePriorityResponse
from app.services.priority_service import PriorityResult, PriorityService


router = APIRouter(prefix="/priorities", tags=["심각도·우선순위"])
service = PriorityService()


def _to_response(result: PriorityResult) -> IssuePriorityResponse:
    group = result.group
    priority = result.priority
    return IssuePriorityResponse(
        issue_group_id=group.id,
        issue_title=group.title,
        category=group.category,
        topic=group.topic,
        inquiry_count=group.inquiry_count,
        impact_score=float(priority.impact_score),
        damage_score=float(priority.damage_score),
        recoverability_score=float(priority.recoverability_score),
        time_sensitivity_score=float(priority.time_sensitivity_score),
        severity_score=float(priority.severity_score),
        severity_level=priority.severity_level,
        volume_score=float(priority.volume_score),
        trend_score=float(priority.trend_score),
        recent_7d_count=priority.recent_7d_count,
        previous_7d_count=priority.previous_7d_count,
        growth_rate_percent=float(priority.growth_rate_percent),
        priority_score=float(priority.priority_score),
        priority_grade=priority.priority_grade,
        priority_rank=priority.priority_rank,
        reasons=priority.reasons,
        calculation_version=priority.calculation_version,
        as_of_utc=priority.as_of_utc,
        calculated_at=priority.calculated_at,
    )


@router.post("/recalculate", response_model=IssuePriorityListResponse)
def recalculate_priorities(
    as_of: datetime | None = Query(
        default=None,
        description="증가 추세 계산 기준 시각. 예: 2026-11-17T16:00:00+09:00",
    ),
    session: Session = Depends(get_db),
) -> IssuePriorityListResponse:
    try:
        run = service.recalculate(session, as_of)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return IssuePriorityListResponse(
        total=len(run.items),
        as_of_utc=run.as_of_utc,
        items=[_to_response(item) for item in run.items],
    )


@router.get("", response_model=IssuePriorityListResponse)
def list_priorities(session: Session = Depends(get_db)) -> IssuePriorityListResponse:
    items = service.list_current(session)
    return IssuePriorityListResponse(
        total=len(items),
        as_of_utc=items[0].priority.as_of_utc if items else None,
        items=[_to_response(item) for item in items],
    )
