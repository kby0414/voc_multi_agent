"""VOC 분류 실행 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import ClassificationRunResponse, IssueGroupResponse
from app.services.classification_service import ClassificationService


router = APIRouter(prefix="/analysis", tags=["분류·그룹화"])
service = ClassificationService()


@router.post("/classify", response_model=ClassificationRunResponse)
def classify_pending_vocs(
    limit: int = Query(default=500, ge=1, le=5_000),
    session: Session = Depends(get_db),
) -> ClassificationRunResponse:
    result = service.run_pending(session, limit)
    return ClassificationRunResponse(
        requested_limit=limit,
        processed_count=result.processed_count,
        created_group_count=result.created_group_count,
        updated_group_count=result.updated_group_count,
        groups=[IssueGroupResponse.model_validate(group) for group in result.groups],
    )


@router.post("/classify/{voc_id}", response_model=ClassificationRunResponse)
def classify_single_voc(
    voc_id: int,
    session: Session = Depends(get_db),
) -> ClassificationRunResponse:
    result = service.run_voc(session, voc_id)
    if result.processed_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="VOC가 없거나 이미 분석되었습니다.",
        )
    return ClassificationRunResponse(
        requested_limit=1,
        processed_count=result.processed_count,
        created_group_count=result.created_group_count,
        updated_group_count=result.updated_group_count,
        groups=[IssueGroupResponse.model_validate(group) for group in result.groups],
    )
