"""
Pytest configuration — MedFlow AI.

Quan trọng: set env TRƯỚC khi import app (để config dùng mock + DB test).
"""
import os
import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Dùng forward-slash để đường dẫn URL khớp tuyệt đối với file hệ thống
_DB_PATH = str(BACKEND_DIR / "test_medflow.db").replace("\\", "/")

# Override env trước khi import config (load_dotenv(override=False) nên env thắng .env)
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("MEDFLOW_INTEGRATION_MODE", "mock")
os.environ.setdefault("MEDFLOW_DB_URL", f"sqlite:///{_DB_PATH}")

import pytest  # noqa: E402

from app.db.models import Base, init_db, engine, SessionLocal  # noqa: E402
from app.db.seed import seed_database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    """Luôn reset DB sạch (drop_all + create_all + seed) để test deterministic."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_database()
    yield
    engine.dispose()
    try:
        os.remove(BACKEND_DIR / "test_medflow.db")
    except OSError:
        pass


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state in-memory giữa các test (orchestrator sessions + llm)."""
    from app.orchestrator import orchestrator
    from app.services.llm_service import llm_service
    orchestrator.sessions.clear()
    llm_service.conversations.clear()
    yield
