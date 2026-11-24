"""선택적으로 OpenAI API를 호출하는 얇은 어댑터."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI


class LLMService:
    def __init__(
        self,
        mode: str,
        model: str = "gpt-5-mini",
        logger: Callable[[str], None] | None = None,
    ) -> None:
        load_dotenv()
        self.mode = mode
        self.model = model
        self.logger = logger or (lambda _: None)
        self.client: OpenAI | None = None
        if mode == "ai" and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI()
        elif mode == "ai":
            self.logger("    API 키가 없어 규칙 기반 결과를 사용합니다.")

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def ask_json(self, prompt_path: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.client:
            return None

        try:
            prompt = prompt_path.read_text(encoding="utf-8")
            response = self.client.responses.create(
                model=self.model,
                instructions=prompt,
                input=json.dumps(payload, ensure_ascii=False),
            )
            return self._parse_json(response.output_text)
        except Exception as exc:  # 네트워크/API 오류는 규칙 기반 결과로 안전하게 대체
            self.logger(f"    AI 보강 실패: {type(exc).__name__}. 규칙 기반 결과를 유지합니다.")
            return None

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | None:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        try:
            value = json.loads(cleaned)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                return None
            try:
                value = json.loads(match.group(0))
                return value if isinstance(value, dict) else None
            except json.JSONDecodeError:
                return None
