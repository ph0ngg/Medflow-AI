# TECH SPEC — Technical Specification

## Stack
| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2.0, SQLite |
| Frontend | React 18, TypeScript, Vite |
| AI models | ONNX Runtime (YOLOv8 face, ArcFace, FAISS) — `backend/ai_modules/` |
| STT | PhoWhisper / Whisper (transformers) |
| TTS | Edge TTS (giọng vi-VN) |
| OCR | PaddleOCR (mock fallback) |
| LLM | Cohere / OpenAI / Gemini / mock (offline) |
| Test | pytest + FastAPI TestClient |

## Module map (backend)
```
app/
├── config.py         # env/config (load backend/.env)
├── rules.py          # clinical safety + business rules (testable)
├── session.py        # SessionState enum + KioskSession dataclass
├── orchestrator.py   # state machine, điều phối luồng
├── api/              # kiosk.py, admin.py
├── db/               # models.py, seed.py
├── services/         # llm, triage, face, stt, tts, ocr
└── adapters/         # base + his/insurance/queue/payment/identity (mock)
```

## Frontend (React)
```
src/
├── api.ts            # client gọi /api/kiosk
├── types.ts          # shared types (mirror backend contract)
├── hooks/useKiosk.ts # state machine + actions
├── components/       # CameraFeed, VoiceButton, ui (BigButton/Card/Ticket...)
├── screens/          # 10 screen files (15 màn hình PRD)
└── App.tsx, styles.css
```

## Data flow (voice)
Mic → `VoiceButton` (webm) → `POST /voice-message` → ffmpeg → WAV 16k → STT → text → orchestrator → LLM/rules → response (→ TTS).

## Non-functional
- Kiosk-friendly UI: chữ lớn, tương phản cao, nút lớn.
- Session timeout + auto reset (privacy).
- Backend chạy được khi thiếu model nặng (degrade).
