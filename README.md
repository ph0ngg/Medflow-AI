# MedFlow AI

Kiosk AI hội thoại hỗ trợ **tiếp đón, phân luồng và điều phối bệnh nhân** tại bệnh viện.

Người bệnh **nói nhu cầu bằng tiếng Việt đời thường**; hệ thống xác thực danh tính (khuôn mặt/CCCD),
khai thác triệu chứng, đề xuất khoa khám (AI + rule, **không chẩn đoán**), kiểm tra hàng đợi,
thanh toán (mock) và cấp số thứ tự — kèm luồng cảnh báo red-flag.

> ⚕️ Prototype — không thay thế HIS/EMR, không chẩn đoán/kê đơn/điều trị.

## Kiến trúc (tóm tắt)
```
Kiosk UI (React/Vite)  →  Backend API (FastAPI)  →  AI & Rules  →  Data & Adapters (mock)
frontend/src/             backend/app/              services/       adapters/ + db/
```

Chi tiết: `docs/ARCHITECTURE.md`, `docs/TECH_SPEC.md`.

## Cấu trúc thư mục
```
backend/            FastAPI + ai_modules (face model ONNX)
frontend/           React 18 + TS + Vite
docs/               Bộ tài liệu spec-driven (PRD, SRS, UX, API, AI, ...)
tests/              pytest
legacy/             Code cũ (tham khảo)
AGENTS.md           Luật cho AI coding agent
```

## Yêu cầu
- Python 3.10+ (khuyến nghị conda env `myenv` đã cài sẵn dependencies).
- Node.js 18+.
- (Tùy chọn) `ffmpeg` cho chuyển đổi audio STT.

## Quick start

### 1. Backend (FastAPI :8080)
```bash
conda activate myenv          # hoặc môi trường đã cài requirements
cd backend
python -m uvicorn app.main:app --reload --port 8080
```
- API docs: http://localhost:8080/docs
- Health: http://localhost:8080/api/health

### 2. Frontend (Vite :5173)
```bash
cd frontend
npm install
npm run dev
```
Mở http://localhost:5173 (Vite proxy `/api` → `:8080`).

### 3. Test
```bash
python -m pytest tests -v
```

## Cấu hình
Biến môi trường đặt trong `backend/.env` (không commit). Các biến chính:
- `LLM_PROVIDER`: `mock` (mặc định, offline) | `cohere` | `openai` | `gemini`
- `MEDFLOW_DB_URL`: SQLite URL
- `MEDFLOW_INTEGRATION_MODE`: `mock` (prototype)
- `STT_PROVIDER`: `phowhisper` | `whisper`
- `TTS_PROVIDER`: `edge`

## Luồng chính (prototype)
1. **Idle** → camera phát hiện người.
2. **Xác thực**: nhận diện mặt (bệnh nhân cũ) hoặc CCCD/mã bệnh nhân (mới/dự phòng).
3. **Hồ sơ**: xác nhận thông tin + BHYT + lịch hẹn.
4. **Hội thoại**: nói/ gõ nhu cầu → AI khai thác triệu chứng (nhiều lượt).
5. **Đề xuất khoa** + **hàng đợi** → bệnh nhân xác nhận.
6. **Thanh toán** (mock) → **xác nhận cuối** → **cấp số** + wayfinding.
7. **Red-flag** → dừng luồng, hướng dẫn gặp nhân viên y tế.

## Tài liệu
Xem `docs/` — PRD, SRS, UX_SPEC, USER_FLOWS, TECH_SPEC, ARCHITECTURE, DATA_MODEL, API_SPEC, AI_SPEC, DESIGN_SYSTEM, TEST_SPEC, DECISIONS, ISSUES.
