"""고객 문의 한 건의 저장부터 분석까지 서버에서 이어서 처리한다."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.voc import VOC
from app.schemas.voc import CustomerVOCIntake, VOCCreate
from app.services.classification_service import ClassificationService
from app.services.priority_service import PriorityService
from app.services.voc_service import VOCService


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CustomerIntakeResult:
    voc: VOC
    processing_status: str


class IntakeService:
    def __init__(
        self,
        voc_service: VOCService | None = None,
        classification_service: ClassificationService | None = None,
        priority_service: PriorityService | None = None,
    ) -> None:
        self.voc_service = voc_service or VOCService()
        self.classification_service = classification_service or ClassificationService()
        self.priority_service = priority_service or PriorityService()

    def receive_customer_voc(
        self, session: Session, payload: CustomerVOCIntake
    ) -> CustomerIntakeResult:
        voc = self.voc_service.create(
            session,
            VOCCreate(
                channel="웹사이트",
                content=payload.content,
                received_at=datetime.now(timezone.utc),
                game_name=payload.game_name,
                platform=payload.platform,
                game_version="customer-portal",
                metadata={"source": "customer_portal"},
            ),
        )

        try:
            classification = self.classification_service.run_voc(session, voc.id)
            if classification.processed_count == 0:
                return CustomerIntakeResult(voc=voc, processing_status="분석 대기")
            self.priority_service.recalculate(session)
        except Exception:
            session.rollback()
            logger.exception("VOC %s 자동 분석 중 오류가 발생했습니다.", voc.id)
            return CustomerIntakeResult(voc=voc, processing_status="분석 대기")

        return CustomerIntakeResult(voc=voc, processing_status="분석 완료")
