"""VOC 등록과 조회에 사용하는 FastAPI 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VOCCreate(BaseModel):
    external_id: str | None = Field(default=None, max_length=100)
    channel: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=2, max_length=10_000)
    received_at: datetime
    game_name: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=50)
    game_version: str | None = Field(default=None, max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("received_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at에는 +09:00 또는 Z 같은 시간대 정보가 필요합니다.")
        return value


class VOCResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    channel: str
    content_masked: str
    received_at_utc: datetime
    game_name: str | None
    platform: str | None
    game_version: str | None
    source_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CustomerVOCIntake(BaseModel):
    """고객 문의 페이지에서 받는 최소 입력값."""

    game_name: str = Field(min_length=1, max_length=100)
    platform: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=2, max_length=10_000)


class VOCReceiptResponse(BaseModel):
    voc_id: int
    receipt_number: str
    processing_status: str
    message: str


class AdminVOCResponse(BaseModel):
    id: int
    receipt_number: str
    channel: str
    content_masked: str
    received_at_utc: datetime
    game_name: str | None
    platform: str | None
    processing_status: str
    is_recent: bool
    category: str | None = None
    topic: str | None = None
    confidence: float | None = None
    issue_group_id: int | None = None
    issue_group_title: str | None = None
    inquiry_count: int | None = None
    severity_score: float | None = None
    severity_level: str | None = None
    priority_score: float | None = None
    priority_grade: str | None = None
    priority_rank: int | None = None
    reasons: list[str] = Field(default_factory=list)


class AdminVOCListResponse(BaseModel):
    total: int
    recent_count: int
    offset: int
    limit: int
    items: list[AdminVOCResponse]


class VOCListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[VOCResponse]


class VOCBulkCreate(BaseModel):
    items: list[VOCCreate] = Field(min_length=1, max_length=1_000)


class VOCBulkResponse(BaseModel):
    requested_count: int
    created_count: int
    skipped_duplicate_count: int
    items: list[VOCResponse]
