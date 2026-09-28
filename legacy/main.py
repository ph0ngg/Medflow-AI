"""
MedFlow AI - Kiosk AI hội thoại hỗ trợ tiếp đón bệnh nhân.

Entry point FastAPI.
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Đảm bảo medflow-ai có độ ưu tiên cao nhất (để `from config import ...` tìm đúng)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routes import kiosk_router, admin_router


# ── Lifespan (startup/shutdown) ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo database và seed data khi server start."""
    init_db()
    from database.seed import seed_database
    from database.models import SessionLocal, Department
    db = SessionLocal()
    try:
        if db.query(Department).count() == 0:
            seed_database()
    finally:
        db.close()
    print("🚀 MedFlow AI đã sẵn sàng!")
    yield  # Server chạy ở đây
    print("👋 MedFlow AI đã dừng.")


# ── Khởi tạo App ──────────────────────────────────────
app = FastAPI(
    title="MedFlow AI",
    description="Kiosk AI hội thoại hỗ trợ tiếp đón, phân luồng và điều phối bệnh nhân",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(kiosk_router)
app.include_router(admin_router)

# Static files (kiosk UI) - dùng absolute path để tránh lỗi working directory
STATIC_DIR = str(Path(__file__).resolve().parent / "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Redirect đến kiosk UI."""
    from fastapi.responses import FileResponse
    return FileResponse(str(Path(__file__).resolve().parent / "static/index.html"))


if __name__ == "__main__":
    import uvicorn
    import os
    os.chdir(str(Path(__file__).resolve().parent))
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
