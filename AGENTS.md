# AGENTS.md — Luật làm việc cho AI coding agent (MedFlow AI)

Tài liệu này là "hợp đồng" để coding agent làm việc ổn định trong repository.
Trước mỗi thay đổi, agent PHẢI đọc PRD + các spec liên quan trong `docs/`.

## Stack (KHÔNG tự ý thay đổi)
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, SQLite (prototype).
- **Frontend**: React 18 + TypeScript + Vite (thư mục `frontend/`).
- **AI models**: ONNX local trong `backend/ai_modules/` (face detection/recognition/FAISS).
- **Test**: pytest (`tests/`).

## Cấu trúc
```
backend/app/        # FastAPI app: config, session, orchestrator, api, db, services, adapters
backend/ai_modules/ # model face (KHÔNG sửa trừ khi thật sự cần)
frontend/src/       # React UI (15 màn hình kiosk)
docs/               # spec-driven
tests/              # pytest
legacy/             # code cũ (chỉ tham khảo, không import)
```

## Quy tắc bắt buộc
1. **Spec-first**: đọc `docs/PRD.md`, `docs/SRS.md`, `docs/AI_SPEC.md` và các doc liên quan trước khi code.
2. **Không tự ý đổi** stack, database schema, architecture khi chưa được phê duyệt (mở ADR trong `docs/DECISIONS/`).
3. **Adapter cho mọi integration thật** (HIS/BHYT/queue/payment/identity): prototype dùng mock trong `backend/app/adapters/`. Không gọi trực tiếp API ngoài từ business logic.
4. **AI an toàn** (PRD mục 9): AI không chẩn đoán/kê đơn; đề xuất khoa = LLM + rule engine (`backend/app/rules.py`); red-flag là rule testable.
5. **Không hard-code** secret/API key/PII. Key để trong `backend/.env` (đã gitignore). Không log PII.
6. **Mỗi thay đổi phải chạy**: backend `python -m pytest tests`, frontend `npm run build`.
7. **Mỗi lỗi phát hiện** phải được chuyển thành test hoặc rule để tránh lặp lại.
8. **Session privacy**: sau mỗi phiên phải reset dữ liệu hiển thị (backend `end_session`, frontend auto-reset).
9. **Tiếng Việt không dấu**: rule matching phải đi qua `app.rules.normalize()` (bỏ dấu) — mọi keyword mới phải test cả có dấu lẫn không dấu.

## Commands
```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload --port 8080   # cần env: conda activate myenv

# Test
python -m pytest tests -v

# Frontend
cd frontend
npm install
npm run dev        # dev server :5173, proxy /api -> :8080
npm run build      # build ra frontend/dist (backend sẽ serve nếu có)
```

## Definition of Done
- [ ] Đọc spec liên quan.
- [ ] Code theo adapter/service/orchestrator layer đúng chỗ.
- [ ] Có test (hoặc cập nhật test) và pass.
- [ ] `npm run build` (nếu đụng frontend) không lỗi.
- [ ] Không thêm secret/PII vào repo.
