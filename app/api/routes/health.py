"""FastAPI와 SQLite 연결 상태를 확인하는 엔드포인트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.db.session import check_database_connection


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["상태 확인"])


@router.get("", summary="FastAPI 서버 상태 확인")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "FastAPI 서버가 정상 실행 중입니다.",
    }


@router.get("/database", summary="SQLite 연결 상태 확인")
def database_health() -> dict[str, str]:
    try:
        database = check_database_connection()
    except Exception as exc:
        logger.exception("SQLite 연결 확인에 실패했습니다.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQLite 파일에 연결할 수 없습니다. 파일 경로와 권한을 확인해 주세요.",
        ) from exc

    return {
        "status": "ok",
        "message": "SQLite 연결이 정상입니다.",
        "database": database["database"],
        "sqlite_version": database["sqlite_version"],
    }
