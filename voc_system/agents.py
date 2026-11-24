"""FastAPI 서비스가 사용하는 VOC 수집·분류 에이전트."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .llm import LLMService
from .models import VOCAnalysis, VOCItem


PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "계정": ("로그인", "계정", "비밀번호", "해킹", "도용", "인증", "정지"),
    "결제": ("결제", "환불", "청약", "영수증", "아이템 구매", "중복", "과금"),
    "기술 오류": ("오류", "버그", "접속", "튕", "팅", "렉", "지연", "설치", "업데이트", "크래시"),
    "게임 운영": ("밸런스", "보상", "이벤트", "점검", "매칭", "드롭률", "운영"),
    "커뮤니티": ("욕설", "괴롭힘", "신고", "채팅", "비매너", "핵", "불법 프로그램"),
    "제안": ("건의", "제안", "개선", "추가해", "바랍니다", "좋겠"),
}

VALID_SEVERITIES = {"낮음", "보통", "높음", "긴급"}

TOPIC_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("중복 결제", ("중복", "두 번", "2번"), "결제 이상"),
    ("환불 요청", ("환불", "청약 철회"), "결제 이상"),
    ("보안 침해", ("해킹", "도용", "탈취"), "계정 보안"),
    ("접속 불가", ("접속 불가", "접속이 안", "로그인이 안"), "실행 안정성"),
    ("강제 종료", ("튕", "팅겨", "팅김", "크래시", "강제 종료", "꺼져"), "실행 안정성"),
    ("성능 저하", ("렉", "지연", "프레임", "느려"), "성능 품질"),
    ("로그인·인증", ("로그인", "인증", "비밀번호"), "이용 편의"),
    ("보상 누락", ("보상", "지급", "누락"), "운영 공정성"),
    ("이용자 괴롭힘", ("욕설", "괴롭힘", "비매너"), "커뮤니티 안전"),
    ("불법 프로그램", ("핵", "불법 프로그램", "치트"), "운영 공정성"),
    ("기능 개선 제안", ("건의", "제안", "개선", "추가해"), "개선 제안"),
)

TOPIC_CATEGORY = {
    "중복 결제": "결제",
    "환불 요청": "결제",
    "보안 침해": "계정",
    "로그인·인증": "계정",
    "접속 불가": "기술 오류",
    "강제 종료": "기술 오류",
    "성능 저하": "기술 오류",
    "보상 누락": "게임 운영",
    "이용자 괴롭힘": "커뮤니티",
    "불법 프로그램": "커뮤니티",
    "기능 개선 제안": "제안",
}

DEFAULT_FEATURE_BY_CATEGORY = {
    "계정": "계정 보안",
    "결제": "결제 이상",
    "기술 오류": "실행 안정성",
    "게임 운영": "운영 공정성",
    "커뮤니티": "커뮤니티 안전",
    "제안": "개선 제안",
    "기타": "이용 편의",
}


def _safe_text(value: Any, default: str = "") -> str:
    return str(value).strip() if value is not None else default


class CollectorAgent:
    agent_code = "A"
    prompt_path = PROMPT_DIR / "agent_a_collector.md"

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

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def run(self, raw: dict[str, Any]) -> VOCItem:
        message = _safe_text(raw.get("message") or raw.get("content") or raw.get("text"))
        if not message:
            raise ValueError("VOC 본문(message)이 비어 있습니다.")

        raw_channel = _safe_text(raw.get("channel") or raw.get("source"), "웹사이트").lower()
        channel = self.CHANNEL_ALIASES.get(raw_channel, raw_channel or "기타")
        voc_id = _safe_text(raw.get("voc_id") or raw.get("id"), f"VOC-{uuid.uuid4().hex[:8].upper()}")
        received_at = _safe_text(
            raw.get("received_at"), datetime.now().astimezone().isoformat(timespec="seconds")
        )
        masked = self.mask_sensitive_data(message)
        item = VOCItem(
            voc_id=voc_id,
            channel=channel,
            message=message,
            masked_message=masked,
            received_at=received_at,
            customer_name=_safe_text(raw.get("customer_name"), "고객"),
            metadata=dict(raw.get("metadata") or {}),
            summary=self._rule_summary(masked),
            customer_intent="문의 내용 확인 및 해결",
        )

        enhanced = self.llm.ask_json(
            self.prompt_path,
            {"channel": channel, "message": masked},
        )
        if enhanced:
            item.summary = _safe_text(enhanced.get("summary"), item.summary)
            item.customer_intent = _safe_text(enhanced.get("customer_intent"), item.customer_intent)
        return item

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        patterns = [
            (r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[이메일 마스킹]"),
            (r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)", "[전화번호 마스킹]"),
            (r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)", "[주민번호 마스킹]"),
            (r"(?<!\d)(?:\d[ -]?){15,16}(?!\d)", "[결제정보 마스킹]"),
        ]
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        return result

    @staticmethod
    def _rule_summary(message: str) -> str:
        compact = " ".join(message.split())
        return compact if len(compact) <= 80 else f"{compact[:77]}..."


class AnalystAgent:
    agent_code = "B"
    prompt_path = PROMPT_DIR / "agent_b_classifier.md"

    NEGATIVE_WORDS = ("화나", "짜증", "최악", "실망", "불편", "억울", "안 돼", "안되", "문제", "피해")
    STRONG_NEGATIVE_WORDS = ("고소", "소송", "사기", "당장", "절대", "탈퇴", "폭발", "죽")
    URGENT_WORDS = ("해킹", "도용", "중복 결제", "미성년", "개인정보", "사라졌", "접속 불가", "결제됐")

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def run(self, item: VOCItem) -> VOCAnalysis:
        text = item.masked_message.lower()
        scores = {
            category: sum(1 for keyword in keywords if keyword in text)
            for category, keywords in CATEGORY_RULES.items()
        }
        category = max(scores, key=scores.get) if max(scores.values(), default=0) else "기타"
        keywords = [keyword for keyword in CATEGORY_RULES.get(category, ()) if keyword in text]

        negative_count = sum(word in text for word in self.NEGATIVE_WORDS)
        strong_count = sum(word in text for word in self.STRONG_NEGATIVE_WORDS)
        if strong_count:
            sentiment = "매우 부정"
        elif negative_count:
            sentiment = "부정"
        elif any(word in text for word in ("감사", "좋", "만족")):
            sentiment = "긍정"
        else:
            sentiment = "중립"

        risk_flags = self._risk_flags(text)
        topic, feature_tag = self._detect_topic(text, category)
        category = TOPIC_CATEGORY.get(topic, category)
        keywords = [
            keyword for keyword in CATEGORY_RULES.get(category, ()) if keyword in text
        ]
        urgency = 1 + min(2, negative_count) + min(2, sum(word in text for word in self.URGENT_WORDS))
        urgency = min(5, max(1, urgency))
        if risk_flags:
            urgency = max(urgency, 4)
        severity = "긴급" if urgency == 5 else "높음" if urgency == 4 else "보통" if urgency >= 2 else "낮음"
        confidence = min(0.98, 0.55 + 0.1 * max(scores.values(), default=0))
        evidence = [f"'{word}' 표현 감지" for word in keywords[:3]] or ["명확한 분류 키워드가 없어 기타로 분류"]

        result = VOCAnalysis(
            category=category,
            topic=topic,
            sentiment=sentiment,
            urgency=urgency,
            severity=severity,
            confidence=round(confidence, 2),
            keywords=keywords[:6],
            feature_tags=[feature_tag],
            risk_flags=risk_flags,
            evidence=evidence,
        )
        enhanced = self.llm.ask_json(
            self.prompt_path,
            {"channel": item.channel, "message": item.masked_message, "rule_result": asdict(result)},
        )
        return self._merge(result, enhanced)

    @staticmethod
    def _detect_topic(text: str, category: str) -> tuple[str, str]:
        for topic, words, feature_tag in TOPIC_RULES:
            if any(word in text for word in words):
                return topic, feature_tag
        return f"{category} 일반 문의", DEFAULT_FEATURE_BY_CATEGORY[category]

    @staticmethod
    def _risk_flags(text: str) -> list[str]:
        checks = {
            "계정 보안": ("해킹", "도용", "탈취"),
            "미성년자 결제": ("미성년", "아이 결제", "자녀 결제"),
            "개인정보": ("개인정보", "주민번호", "신분증"),
            "법적 분쟁": ("고소", "소송", "법적"),
            "안전 위험": ("자해", "죽고", "살해", "죽이"),
        }
        return [label for label, words in checks.items() if any(word in text for word in words)]

    @staticmethod
    def _merge(base: VOCAnalysis, data: dict[str, Any] | None) -> VOCAnalysis:
        if not data:
            return base
        valid_categories = set(CATEGORY_RULES) | {"기타"}
        valid_sentiments = {"매우 부정", "부정", "중립", "긍정"}
        valid_severities = VALID_SEVERITIES
        category = data.get("category") if data.get("category") in valid_categories else base.category
        sentiment = data.get("sentiment") if data.get("sentiment") in valid_sentiments else base.sentiment
        severity = data.get("severity") if data.get("severity") in valid_severities else base.severity
        try:
            urgency = min(5, max(1, int(data.get("urgency", base.urgency))))
            confidence = min(1.0, max(0.0, float(data.get("confidence", base.confidence))))
        except (TypeError, ValueError):
            urgency, confidence = base.urgency, base.confidence
        return VOCAnalysis(
            category=category,
            topic=_safe_text(data.get("topic"), base.topic),
            sentiment=sentiment,
            urgency=urgency,
            severity=severity,
            confidence=round(confidence, 2),
            keywords=[_safe_text(v) for v in data.get("keywords", base.keywords) if _safe_text(v)][:6],
            feature_tags=list(dict.fromkeys(base.feature_tags + [
                _safe_text(v) for v in data.get("feature_tags", []) if _safe_text(v)
            ]))[:5],
            risk_flags=list(dict.fromkeys(base.risk_flags + [
                _safe_text(v) for v in data.get("risk_flags", []) if _safe_text(v)
            ])),
            evidence=[_safe_text(v) for v in data.get("evidence", base.evidence) if _safe_text(v)][:5],
        )


