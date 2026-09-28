"""
MedFlow AI — Kiosk AI hội thoại (entry point FastAPI).

Chạy:  cd backend && uvicorn app.main:app --reload --port 8080
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# backend/ phải nằm trên sys.path để import được `ai_modules` và `app`
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from app.api import kiosk_router, admin_router  # noqa: E402
from app.config import CORS_ORIGINS  # noqa: E402
from app.db.models import init_db, SessionLocal, Department  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.db.seed import seed_database
    db = SessionLocal()
    try:
        if db.query(Department).count() == 0:
            seed_database()
    finally:
        db.close()
    print("🚀 MedFlow AI đã sẵn sàng!")
    yield
    print("👋 MedFlow AI đã dừng.")


app = FastAPI(
    title="MedFlow AI",
    description="Kiosk AI hội thoại hỗ trợ tiếp đón, phân luồng và điều phối bệnh nhân",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kiosk_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health():
    return JSONResponse({"status": "ok", "service": "medflow-ai"})


# ── Serve frontend build (nếu có) ──────────────────────
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def root():
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return JSONResponse({
            "service": "MedFlow AI",
            "message": "Backend đang chạy. Frontend: cd frontend && npm run dev (proxy tới :8080).",
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
