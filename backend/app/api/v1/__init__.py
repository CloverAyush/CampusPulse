from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.reports import router as reports_router
from app.api.v1.issues import router as issues_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(issues_router, prefix="/issues", tags=["issues"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])

