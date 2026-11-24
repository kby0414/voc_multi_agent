"""저장된 VOC를 분류하고 같은 문제 단위로 그룹화한다."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.analysis import IssueGroup, VOCAnalysisRecord, VOCIssueLink
from app.db.models.voc import VOC
from app.repositories.analysis_repository import AnalysisRepository
from voc_system.agents import AnalystAgent
from voc_system.llm import LLMService
from voc_system.models import VOCItem


ANALYSIS_VERSION = "rules-v1"


@dataclass(slots=True)
class ClassificationRun:
    processed_count: int
    created_group_count: int
    updated_group_count: int
    groups: list[IssueGroup]


def build_group_key(game_name: str | None, category: str, topic: str) -> str:
    normalized = "|".join(
        value.strip().lower() for value in (game_name or "공통", category, topic)
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ClassificationService:
    def __init__(self, repository: AnalysisRepository | None = None) -> None:
        self.repository = repository or AnalysisRepository()
        self.analyst = AnalystAgent(LLMService(mode="rules"))

    def run_pending(self, session: Session, limit: int) -> ClassificationRun:
        pending = self.repository.list_unanalyzed(session, limit)
        return self._run_vocs(session, pending)

    def run_voc(self, session: Session, voc_id: int) -> ClassificationRun:
        """방금 등록한 VOC 한 건만 분류해 실시간 시연 결과를 돌려준다."""
        voc = self.repository.get_unanalyzed(session, voc_id)
        return self._run_vocs(session, [voc] if voc is not None else [])

    def _run_vocs(self, session: Session, pending: list[VOC]) -> ClassificationRun:
        created_group_count = 0
        created_group_ids: set[int] = set()
        updated_group_ids: set[int] = set()
        touched_groups: dict[int, IssueGroup] = {}

        for voc in pending:
            result = self.analyst.run(self._to_voc_item(voc))
            group_key = build_group_key(voc.game_name, result.category, result.topic)
            group = self.repository.get_group_by_key(session, group_key)
            if group is None:
                group = IssueGroup(
                    group_key=group_key,
                    title=self._group_title(voc.game_name, result.topic),
                    category=result.category,
                    topic=result.topic,
                    primary_feature=result.feature_tags[0] if result.feature_tags else "기타",
                    status="active",
                    inquiry_count=1,
                    first_detected_at=voc.received_at_utc,
                    last_detected_at=voc.received_at_utc,
                )
                self.repository.add_group(session, group)
                created_group_count += 1
                created_group_ids.add(group.id)
            else:
                group.inquiry_count += 1
                group.first_detected_at = min(group.first_detected_at, voc.received_at_utc)
                group.last_detected_at = max(group.last_detected_at, voc.received_at_utc)
                if group.id not in created_group_ids:
                    updated_group_ids.add(group.id)

            record = VOCAnalysisRecord(
                voc_id=voc.id,
                category=result.category,
                topic=result.topic,
                sentiment=result.sentiment,
                keywords=result.keywords,
                feature_tags=result.feature_tags,
                risk_flags=result.risk_flags,
                evidence=result.evidence,
                confidence=Decimal(str(result.confidence)),
                analysis_version=ANALYSIS_VERSION,
            )
            self.repository.add_analysis(session, record)
            self.repository.add_link(
                session,
                VOCIssueLink(
                    voc_id=voc.id,
                    issue_group_id=group.id,
                    match_method=ANALYSIS_VERSION,
                    match_score=Decimal(str(result.confidence)),
                ),
            )
            touched_groups[group.id] = group

        session.commit()
        for group in touched_groups.values():
            session.refresh(group)
        return ClassificationRun(
            processed_count=len(pending),
            created_group_count=created_group_count,
            updated_group_count=len(updated_group_ids),
            groups=sorted(
                touched_groups.values(),
                key=lambda group: (-group.inquiry_count, group.id),
            ),
        )

    @staticmethod
    def _to_voc_item(voc: VOC) -> VOCItem:
        return VOCItem(
            voc_id=voc.external_id,
            channel=voc.channel,
            message=voc.content_masked,
            masked_message=voc.content_masked,
            received_at=voc.received_at_utc.isoformat(),
            metadata={
                **(voc.source_metadata or {}),
                "game": voc.game_name,
                "platform": voc.platform,
                "game_version": voc.game_version,
            },
        )

    @staticmethod
    def _group_title(game_name: str | None, topic: str) -> str:
        return f"{game_name} - {topic}" if game_name else topic
