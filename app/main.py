"""FastAPI 애플리케이션 생성과 라우터 등록."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.db.session import init_database


settings = get_settings()
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
WEB_DIR = APP_DIR / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="게임 VOC를 문제별로 묶고 해결 우선순위를 분석하는 API",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/voc", status_code=307)


@app.get("/voc", response_class=FileResponse, include_in_schema=False)
def customer_voc() -> FileResponse:
    """고객이 최소한의 정보로 문의를 접수하는 화면."""
    return FileResponse(WEB_DIR / "voc.html")


@app.get("/admin", response_class=FileResponse, include_in_schema=False)
def admin_dashboard() -> FileResponse:
    """운영자가 문제 현황과 해결 우선순위를 확인하는 화면."""
    return FileResponse(WEB_DIR / "dashboard.html")


@app.get("/admin/inbox", response_class=FileResponse, include_in_schema=False)
def admin_inbox() -> FileResponse:
    """최근 VOC와 자동 분석 결과를 함께 확인하는 관리자 문의함."""
    return FileResponse(WEB_DIR / "inbox.html")


@app.get(
    "/dashboard",
    response_class=RedirectResponse,
    include_in_schema=False,
)
def dashboard() -> RedirectResponse:
    """기존 주소를 새 관리자 대시보드 주소로 연결한다."""
    return RedirectResponse(url="/admin", status_code=307)
