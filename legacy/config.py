"""
Cấu hình hệ thống MedFlow AI.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv(Path(__file__).resolve().parent / ".env")

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
AI_MODULES_DIR = BASE_DIR / "ai_modules"

# ── Face Recognition ───────────────────────────────────
FACE_DETECTION_MODEL = str(AI_MODULES_DIR / "face_detection" / "weight" / "yoloface_8n.onnx")
FACE_RECOGNITION_MODEL = str(AI_MODULES_DIR / "face_recognizor" / "weight" / "recognize.onnx")
FAISS_INDEX_PATH = str(AI_MODULES_DIR / "faiss" / "embedding2id.pkl")
FAISS_ID2NAME_PATH = str(AI_MODULES_DIR / "faiss" / "id2name.json")

# ── Database ────────────────────────────────────────────
DATABASE_URL = os.getenv("MEDFLOW_DB_URL", "sqlite:///medflow.db")

# ── Speech-to-Text ──────────────────────────────────────
STT_PROVIDER = os.getenv("STT_PROVIDER", "phowhisper")  # phowhisper | whisper | google | vosk
STT_MODEL = os.getenv("STT_MODEL", "base")               # tiny/base/small/medium/large (cho whisper)
STT_PHOWHISPER_MODEL = os.getenv("STT_PHOWHISPER_MODEL", "vinai/PhoWhisper-small")  # PhoWhisper model

# ── Text-to-Speech ──────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")      # edge | google | vits
TTS_LANG = "vi-VN"

# ── LLM / Conversational AI ─────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "cohere")     # openai | gemini | cohere | local
LLM_MODEL = os.getenv("LLM_MODEL", "command-r-plus")   # command-r-plus (Cohere free) | gpt-4o
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# ── OCR (CCCD) ──────────────────────────────────────────
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "paddle")    # paddle | tesseract

# ── Triage ──────────────────────────────────────────────
EMERGENCY_KEYWORDS = [
    "đau ngực", "khó thở", "vã mồ hôi", "ngất", "bất tỉnh",
    "co giật", "chảy máu nhiều", "đau đầu dữ dội",
]
DEPARTMENT_MAPPING = {
    "Nội tiêu hóa": ["đau bụng", "buồn nôn", "tiêu chảy", "táo bón", "ợ chua"],
    "Nội tim mạch": ["đau ngực", "hồi hộp", "đánh trống ngực", "tăng huyết áp"],
    "Nội hô hấp": ["ho", "khó thở", "đau họng", "sổ mũi", "hắt hơi"],
    "Nội tiết": ["mệt mỏi", "khát nước", "sút cân", "tiểu nhiều"],
    "Cơ xương khớp": ["đau lưng", "đau khớp", "đau cổ", "tê tay chân"],
    "Da liễu": ["ngứa", "nổi mẩn", "phát ban", "mụn"],
    "Tai Mũi Họng": ["đau tai", "ù tai", "viêm mũi", "viêm họng"],
    "Mắt": ["mờ mắt", "đau mắt", "đỏ mắt", "chảy nước mắt"],
}

# ── Server ──────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
