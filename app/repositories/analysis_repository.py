"""미분석 VOC 조회와 문제 그룹 저장 기능."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.analysis import (
    IssueGroup,
    IssuePriority,
    VOCAnalysisRecord,
    VOCIssueLink,
)
from app.db.models.voc import VOC


class AnalysisRepository:
    def list_unanalyzed(self, session: Session, limit: int) -> list[VOC]:
        statement = (
            select(VOC)
            .outerjoin(VOCAnalysisRecord, VOCAnalysisRecord.voc_id == VOC.id)
            .where(VOCAnalysisRecord.id.is_(None))
            .order_by(VOC.received_at_utc.asc(), VOC.id.asc())
            .limit(limit)
        )
        return list(session.scalars(statement))

    def get_unanalyzed(self, session: Session, voc_id: int) -> VOC | None:
        statement = (
            select(VOC)
            .outerjoin(VOCAnalysisRecord, VOCAnalysisRecord.voc_id == VOC.id)
            .where(VOC.id == voc_id, VOCAnalysisRecord.id.is_(None))
        )
        return session.scalar(statement)

    def get_group_by_key(self, session: Session, group_key: str) -> IssueGroup | None:
        return session.scalar(select(IssueGroup).where(IssueGroup.group_key == group_key))

    def list_groups(self, session: Session) -> list[IssueGroup]:
        statement = select(IssueGroup).order_by(
            IssueGroup.inquiry_count.desc(),
            IssueGroup.last_detected_at.desc(),
            IssueGroup.id.asc(),
        )
        return list(session.scalars(statement))

    def count_groups(self, session: Session) -> int:
        return int(session.scalar(select(func.count()).select_from(IssueGroup)) or 0)

    def get_group(self, session: Session, group_id: int) -> IssueGroup | None:
        return session.get(IssueGroup, group_id)

    def list_group_evidence(
        self, session: Session, group_id: int
    ) -> list[tuple[datetime, list[str]]]:
        statement = (
            select(VOC.received_at_utc, VOCAnalysisRecord.risk_flags)
            .join(VOCIssueLink, VOCIssueLink.voc_id == VOC.id)
            .join(VOCAnalysisRecord, VOCAnalysisRecord.voc_id == VOC.id)
            .where(VOCIssueLink.issue_group_id == group_id)
        )
        return [
            (received_at_utc, risk_flags or [])
            for received_at_utc, risk_flags in session.execute(statement)
        ]

    def get_priority(
        self, session: Session, issue_group_id: int
    ) -> IssuePriority | None:
        return session.scalar(
            select(IssuePriority).where(
                IssuePriority.issue_group_id == issue_group_id
            )
        )

    def add_priority(self, session: Session, priority: IssuePriority) -> None:
        session.add(priority)

    def list_priorities(
        self, session: Session
    ) -> list[tuple[IssuePriority, IssueGroup]]:
        statement = (
            select(IssuePriority, IssueGroup)
            .join(IssueGroup, IssueGroup.id == IssuePriority.issue_group_id)
            .order_by(IssuePriority.priority_rank.asc(), IssueGroup.id.asc())
        )
        return [(priority, group) for priority, group in session.execute(statement)]

    def add_analysis(self, session: Session, record: VOCAnalysisRecord) -> None:
        session.add(record)

    def add_group(self, session: Session, group: IssueGroup) -> None:
        session.add(group)
        session.flush()

    def add_link(self, session: Session, link: VOCIssueLink) -> None:
        session.add(link)
