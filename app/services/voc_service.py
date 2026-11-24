"""VOC 입력 정규화, 개인정보 마스킹과 저장 흐름."""

from __future__ import annotations

import uuid
from datetime import timezone

from sqlalchemy.orm import Session

from app.db.models.voc import VOC
from app.repositories.voc_repository import VOCRepository
from app.schemas.voc import VOCCreate
from voc_system.agents import CollectorAgent


CHANNEL_ALIASES = {
    "web": "웹사이트",
    "website": "웹사이트",
    "웹": "웹사이트",
    "웹사이트": "웹사이트",
    "phone": "전화상담",
    "call": "전화상담",
    "전화": "전화상담",
    "전화상담": "전화상담",
    "sns": "SNS",
    "social": "SNS",
    "소셜": "SNS",
}


class VOCService:
    def __init__(self, repository: VOCRepository | None = None) -> None:
        self.repository = repository or VOCRepository()

    def create(self, session: Session, payload: VOCCreate) -> VOC:
        raw_channel = payload.channel.strip().lower()
        channel = CHANNEL_ALIASES.get(raw_channel, payload.channel.strip())
        external_id = payload.external_id or f"VOC-{uuid.uuid4().hex[:12].upper()}"
        received_at_utc = payload.received_at.astimezone(timezone.utc).replace(tzinfo=None)

        voc = VOC(
            external_id=external_id,
            channel=channel,
            content_masked=CollectorAgent.mask_sensitive_data(payload.content.strip()),
            received_at_utc=received_at_utc,
            game_name=payload.game_name,
            platform=payload.platform,
            game_version=payload.game_version,
            source_metadata=payload.metadata,
        )
        return self.repository.create(session, voc)
