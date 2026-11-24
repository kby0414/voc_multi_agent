"""SQLAlchemy 엔진, 세션과 SQLite 연결·초기화 기능."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLite에 저장할 모든 ORM 모델의 기반 클래스."""


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 엔드포인트에 SQLite 세션을 제공한다."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    """등록된 ORM 모델을 기준으로 누락된 SQLite 테이블을 생성한다."""
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def check_database_connection() -> dict[str, Any]:
    """연결된 SQLite 파일과 버전을 반환한다."""
    with get_engine().connect() as connection:
        version = connection.execute(text("SELECT sqlite_version()")).scalar_one()
        database_rows = connection.execute(text("PRAGMA database_list")).mappings()
        main_database = next(row for row in database_rows if row["name"] == "main")
    return {
        "database": str(main_database["file"]),
        "sqlite_version": str(version),
    }
