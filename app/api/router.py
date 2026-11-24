"""도메인 API 라우터를 한곳에 모은다."""

from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.issues import router as issues_router
from app.api.routes.priorities import router as priorities_router
from app.api.routes.vocs import router as vocs_router


api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(vocs_router)
api_router.include_router(analysis_router)
api_router.include_router(issues_router)
api_router.include_router(priorities_router)
