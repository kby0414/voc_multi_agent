"""VOC 분석 결과, 문제 그룹과 그룹 연결 모델."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


PRIMARY_KEY_TYPE = BigInteger().with_variant(Integer, "sqlite")


class VOCAnalysisRecord(Base):
    __tablename__ = "voc_analyses"
    __table_args__ = (Index("ix_voc_analyses_category_topic", "category", "topic"),)

    id: Mapped[int] = mapped_column(
        PRIMARY_KEY_TYPE, primary_key=True, autoincrement=True
    )
    voc_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vocs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    feature_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    analysis_version: Mapped[str] = mapped_column(String(30), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )


class IssueGroup(Base):
    __tablename__ = "issue_groups"
    __table_args__ = (
        Index("ix_issue_groups_category", "category"),
        Index("ix_issue_groups_status_count", "status", "inquiry_count"),
    )

    id: Mapped[int] = mapped_column(
        PRIMARY_KEY_TYPE, primary_key=True, autoincrement=True
    )
    group_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_feature: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    inquiry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class VOCIssueLink(Base):
    __tablename__ = "voc_issue_links"
    __table_args__ = (
        UniqueConstraint("voc_id", name="uq_voc_issue_links_voc_id"),
        Index("ix_voc_issue_links_group_id", "issue_group_id"),
    )

    id: Mapped[int] = mapped_column(
        PRIMARY_KEY_TYPE, primary_key=True, autoincrement=True
    )
    voc_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vocs.id", ondelete="CASCADE"),
        nullable=False,
    )
    issue_group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("issue_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_method: Mapped[str] = mapped_column(String(30), nullable=False)
    match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )


class IssuePriority(Base):
    __tablename__ = "issue_priorities"
    __table_args__ = (
        UniqueConstraint("issue_group_id", name="uq_issue_priorities_issue_group_id"),
        Index("ix_issue_priorities_rank", "priority_rank"),
        Index("ix_issue_priorities_score", "priority_score"),
    )

    id: Mapped[int] = mapped_column(
        PRIMARY_KEY_TYPE, primary_key=True, autoincrement=True
    )
    issue_group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("issue_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    impact_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    damage_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    recoverability_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    time_sensitivity_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    severity_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    severity_level: Mapped[str] = mapped_column(String(10), nullable=False)
    volume_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    trend_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    recent_7d_count: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_7d_count: Mapped[int] = mapped_column(Integer, nullable=False)
    growth_rate_percent: Mapped[Decimal] = mapped_column(Numeric(9, 2), nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    priority_grade: Mapped[str] = mapped_column(String(5), nullable=False)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    calculation_version: Mapped[str] = mapped_column(String(30), nullable=False)
    as_of_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
