"""분류 실행 결과와 문제 그룹 응답 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IssueGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    topic: str
    primary_feature: str
    status: str
    inquiry_count: int
    first_detected_at: datetime
    last_detected_at: datetime
    created_at: datetime
    updated_at: datetime


class ClassificationRunResponse(BaseModel):
    requested_limit: int
    processed_count: int
    created_group_count: int
    updated_group_count: int
    groups: list[IssueGroupResponse]


class IssueGroupListResponse(BaseModel):
    total: int
    items: list[IssueGroupResponse]


class IssuePriorityResponse(BaseModel):
    issue_group_id: int
    issue_title: str
    category: str
    topic: str
    inquiry_count: int
    impact_score: float
    damage_score: float
    recoverability_score: float
    time_sensitivity_score: float
    severity_score: float
    severity_level: str
    volume_score: float
    trend_score: float
    recent_7d_count: int
    previous_7d_count: int
    growth_rate_percent: float
    priority_score: float
    priority_grade: str
    priority_rank: int
    reasons: list[str]
    calculation_version: str
    as_of_utc: datetime
    calculated_at: datetime


class IssuePriorityListResponse(BaseModel):
    total: int
    as_of_utc: datetime | None
    items: list[IssuePriorityResponse]
