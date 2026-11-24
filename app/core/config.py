"""환경변수에서 FastAPI와 SQLite 설정을 읽는다."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_env: str
    sqlite_database_path: Path

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="sqlite+pysqlite",
            database=str(self.sqlite_database_path),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    configured_path = Path(os.getenv("SQLITE_DATABASE_PATH", "data/game_voc.db"))
    database_path = (
        configured_path
        if configured_path.is_absolute()
        else project_root / configured_path
    )
    return Settings(
        app_name=os.getenv("APP_NAME", "게임 VOC 이슈 우선순위 분석 시스템"),
        app_env=os.getenv("APP_ENV", "development"),
        sqlite_database_path=database_path.resolve(),
    )
