"""생성된 문제 그룹 조회 API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import IssueGroupListResponse, IssueGroupResponse


router = APIRouter(prefix="/issues", tags=["문제 그룹"])
repository = AnalysisRepository()


@router.get("", response_model=IssueGroupListResponse)
def list_issue_groups(session: Session = Depends(get_db)) -> IssueGroupListResponse:
    groups = repository.list_groups(session)
    return IssueGroupListResponse(
        total=repository.count_groups(session),
        items=[IssueGroupResponse.model_validate(group) for group in groups],
    )


@router.get("/{group_id}", response_model=IssueGroupResponse)
def get_issue_group(group_id: int, session: Session = Depends(get_db)) -> IssueGroupResponse:
    group = repository.get_group(session, group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문제 그룹을 찾을 수 없습니다.",
        )
    return IssueGroupResponse.model_validate(group)
