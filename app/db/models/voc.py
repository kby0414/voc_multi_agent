"""SQLite에 저장하는 원본 VOC 모델."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


PRIMARY_KEY_TYPE = BigInteger().with_variant(Integer, "sqlite")


class VOC(Base):
    __tablename__ = "vocs"
    __table_args__ = (
        UniqueConstraint("channel", "external_id", name="uq_vocs_channel_external_id"),
        Index("ix_vocs_received_at_utc", "received_at_utc"),
        Index("ix_vocs_platform", "platform"),
    )

    id: Mapped[int] = mapped_column(
        PRIMARY_KEY_TYPE, primary_key=True, autoincrement=True
    )
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    content_masked: Mapped[str] = mapped_column(Text, nullable=False)
    received_at_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    game_name: Mapped[str | None] = mapped_column(String(100))
    platform: Mapped[str | None] = mapped_column(String(50))
    game_version: Mapped[str | None] = mapped_column(String(50))
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
