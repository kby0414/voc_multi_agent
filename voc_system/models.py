"""에이전트 사이에서 공유하는 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class VOCItem:
    voc_id: str
    channel: str
    message: str
    received_at: str
    customer_name: str = "고객"
    metadata: dict[str, Any] = field(default_factory=dict)
    masked_message: str = ""
    summary: str = ""
    customer_intent: str = ""


@dataclass(slots=True)
class VOCAnalysis:
    category: str
    topic: str
    sentiment: str
    urgency: int
    severity: str
    confidence: float
    keywords: list[str] = field(default_factory=list)
    feature_tags: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
