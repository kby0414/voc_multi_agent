"""VOC 테이블의 저장과 조회 기능."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.voc import VOC
from app.db.models.analysis import (
    IssueGroup,
    IssuePriority,
    VOCAnalysisRecord,
    VOCIssueLink,
)


class DuplicateVOCError(ValueError):
    """같은 채널과 외부 문의 ID가 이미 저장된 경우."""


class VOCRepository:
    def create(self, session: Session, voc: VOC) -> VOC:
        session.add(voc)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateVOCError(
                "같은 채널과 external_id를 가진 VOC가 이미 존재합니다."
            ) from exc
        session.refresh(voc)
        return voc

    def get(self, session: Session, voc_id: int) -> VOC | None:
        return session.get(VOC, voc_id)

    def list(self, session: Session, offset: int, limit: int) -> list[VOC]:
        statement = (
            select(VOC)
            .order_by(VOC.received_at_utc.desc(), VOC.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(statement))

    def count(self, session: Session) -> int:
        statement = select(func.count()).select_from(VOC)
        return int(session.scalar(statement) or 0)

    def list_with_analysis(
        self, session: Session, offset: int, limit: int
    ) -> list[
        tuple[
            VOC,
            VOCAnalysisRecord | None,
            IssueGroup | None,
            IssuePriority | None,
        ]
    ]:
        statement = (
            select(VOC, VOCAnalysisRecord, IssueGroup, IssuePriority)
            .outerjoin(VOCAnalysisRecord, VOCAnalysisRecord.voc_id == VOC.id)
            .outerjoin(VOCIssueLink, VOCIssueLink.voc_id == VOC.id)
            .outerjoin(IssueGroup, IssueGroup.id == VOCIssueLink.issue_group_id)
            .outerjoin(IssuePriority, IssuePriority.issue_group_id == IssueGroup.id)
            .order_by(VOC.received_at_utc.desc(), VOC.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.execute(statement).tuples())

    def get_with_analysis(
        self, session: Session, voc_id: int
    ) -> tuple[
        VOC,
        VOCAnalysisRecord | None,
        IssueGroup | None,
        IssuePriority | None,
    ] | None:
        statement = (
            select(VOC, VOCAnalysisRecord, IssueGroup, IssuePriority)
            .outerjoin(VOCAnalysisRecord, VOCAnalysisRecord.voc_id == VOC.id)
            .outerjoin(VOCIssueLink, VOCIssueLink.voc_id == VOC.id)
            .outerjoin(IssueGroup, IssueGroup.id == VOCIssueLink.issue_group_id)
            .outerjoin(IssuePriority, IssuePriority.issue_group_id == IssueGroup.id)
            .where(VOC.id == voc_id)
        )
        return session.execute(statement).tuples().one_or_none()

    def count_received_since(self, session: Session, since_utc: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(VOC)
            .where(VOC.received_at_utc >= since_utc)
        )
        return int(session.scalar(statement) or 0)
