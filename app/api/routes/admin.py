"""관리자 실시간 문의함 조회 API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models.analysis import IssueGroup, IssuePriority, VOCAnalysisRecord
from app.db.models.voc import VOC
from app.db.session import get_db
from app.repositories.voc_repository import VOCRepository
from app.schemas.voc import AdminVOCListResponse, AdminVOCResponse


router = APIRouter(prefix="/admin/vocs", tags=["관리자 문의함"])
repository = VOCRepository()
RECENT_WINDOW = timedelta(minutes=10)


def _recent_since() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) - RECENT_WINDOW


def _processing_status(
    analysis: VOCAnalysisRecord | None,
    priority: IssuePriority | None,
) -> str:
    if analysis is None:
        return "분석 대기"
    if analysis.category == "기타" or float(analysis.confidence) < 0.55:
        return "검토 필요"
    if priority is None:
        return "우선순위 계산 중"
    return "분석 완료"


def _to_response(
    row: tuple[
        VOC,
        VOCAnalysisRecord | None,
        IssueGroup | None,
        IssuePriority | None,
    ],
    recent_since: datetime,
) -> AdminVOCResponse:
    voc, analysis, group, priority = row
    return AdminVOCResponse(
        id=voc.id,
        receipt_number=voc.external_id,
        channel=voc.channel,
        content_masked=voc.content_masked,
        received_at_utc=voc.received_at_utc,
        game_name=voc.game_name,
        platform=voc.platform,
        processing_status=_processing_status(analysis, priority),
        is_recent=voc.received_at_utc >= recent_since,
        category=analysis.category if analysis else None,
        topic=analysis.topic if analysis else None,
        confidence=float(analysis.confidence) if analysis else None,
        issue_group_id=group.id if group else None,
        issue_group_title=group.title if group else None,
        inquiry_count=group.inquiry_count if group else None,
        severity_score=float(priority.severity_score) if priority else None,
        severity_level=priority.severity_level if priority else None,
        priority_score=float(priority.priority_score) if priority else None,
        priority_grade=priority.priority_grade if priority else None,
        priority_rank=priority.priority_rank if priority else None,
        reasons=list(priority.reasons or []) if priority else [],
    )


@router.get("", response_model=AdminVOCListResponse)
def list_admin_vocs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
) -> AdminVOCListResponse:
    recent_since = _recent_since()
    rows = repository.list_with_analysis(session, offset=offset, limit=limit)
    return AdminVOCListResponse(
        total=repository.count(session),
        recent_count=repository.count_received_since(session, recent_since),
        offset=offset,
        limit=limit,
        items=[_to_response(row, recent_since) for row in rows],
    )


@router.get("/{voc_id}", response_model=AdminVOCResponse)
def get_admin_voc(
    voc_id: int,
    session: Session = Depends(get_db),
) -> AdminVOCResponse:
    row = repository.get_with_analysis(session, voc_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VOC를 찾을 수 없습니다.",
        )
    return _to_response(row, _recent_since())
