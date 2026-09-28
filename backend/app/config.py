"""
Cấu hình hệ thống MedFlow AI.

Tất cả giá trị có thể override qua biến môi trường hoặc file `.env`.
Không hard-code secret trong source code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────
# backend/  (cha của package `app`)
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load biến môi trường từ backend/.env (KHÔNG override biến đã có sẵn)
load_dotenv(BACKEND_DIR / ".env", override=False)

AI_MODULES_DIR = BACKEND_DIR / "ai_modules"
FACE_DETECTION_MODEL = str(AI_MODULES_DIR / "face_detection" / "weight" / "yoloface_8n.onnx")
FACE_RECOGNITION_MODEL = str(AI_MODULES_DIR / "face_recognizor" / "weight" / "recognize.onnx")
FAISS_INDEX_PATH = str(AI_MODULES_DIR / "faiss" / "embedding2id.pkl")
FAISS_ID2NAME_PATH = str(AI_MODULES_DIR / "faiss" / "id2name.json")

# ── Database ────────────────────────────────────────────
DATABASE_URL = os.getenv("MEDFLOW_DB_URL", f"sqlite:///{BACKEND_DIR / 'medflow.db'}")

# ── Integration mode ────────────────────────────────────
# "mock" (prototype) | tên adapter thật sau này
INTEGRATION_MODE = os.getenv("MEDFLOW_INTEGRATION_MODE", "mock")

# ── Speech-to-Text ──────────────────────────────────────
STT_PROVIDER = os.getenv("STT_PROVIDER", "openai")    # openai | phowhisper | whisper
STT_MODEL = os.getenv("STT_MODEL", "base")
STT_PHOWHISPER_MODEL = os.getenv("STT_PHOWHISPER_MODEL", "vinai/PhoWhisper-small")
STT_OPENAI_MODEL = os.getenv("STT_OPENAI_MODEL", "gpt-transcribe")

# ── Text-to-Speech ──────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "openai")    # openai | edge
TTS_LANG = "vi-VN"
TTS_OPENAI_MODEL = os.getenv("TTS_OPENAI_MODEL", "gpt-4o-mini-tts")
TTS_OPENAI_VOICE = os.getenv("TTS_OPENAI_VOICE", "alloy")

# ── LLM / Conversational AI ─────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")      # mock | cohere | openai | gemini
LLM_MODEL = os.getenv("LLM_MODEL", "command-r7b-12-2024")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# ── OCR (CCCD) ──────────────────────────────────────────
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "mock")      # mock | paddle | tesseract

# ── Server ──────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ── Session / Privacy ───────────────────────────────────
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "180"))
