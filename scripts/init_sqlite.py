"""SQLite 데이터베이스와 전체 테이블을 생성하고 상태를 출력한다."""

from __future__ import annotations

import sys

from sqlalchemy import inspect

from app.db.session import check_database_connection, get_engine, init_database


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    init_database()
    database = check_database_connection()
    tables = inspect(get_engine()).get_table_names()

    print("SQLite 초기화: 정상")
    print(f"데이터베이스 파일: {database['database']}")
    print(f"SQLite 버전: {database['sqlite_version']}")
    print("생성된 테이블:")
    for table in tables:
        print(f"- {table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
