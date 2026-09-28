"""API package — MedFlow AI."""
from app.api.kiosk import router as kiosk_router
from app.api.admin import router as admin_router

__all__ = ["kiosk_router", "admin_router"]
