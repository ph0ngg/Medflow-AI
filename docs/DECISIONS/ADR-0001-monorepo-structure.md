# ADR-0001: Monorepo structure (backend/ + frontend/ + docs/ + tests/)

- **Trạng thái**: Accepted
- **Ngày**: 2026-08-30

## Bối cảnh
Project cũ đặt mọi thứ phẳng ở `medflow-ai/` (config, main, orchestrator, database, routes,
services, static, ai_modules). PRD v2 yêu cầu spec-driven + tách frontend React/Vite.

## Quyết định
Tổ chức monorepo:
```
backend/    FastAPI + ai_modules (model face)
frontend/   React 18 + TS + Vite
docs/       spec-driven
tests/      pytest
legacy/     code cũ (tham khảo)
```

## Lý do
- Tách rõ backend/frontend, dễ phát triển song song.
- `legacy/` giữ code cũ để tham khảo, không xóa.
- `docs/` là nguồn context ổn định cho coding agent.

## Hệ quả
- `backend/app/main.py` insert `backend/` vào `sys.path` để import `ai_modules` và `app`.
- Frontend dev dùng Vite proxy `/api` → `:8080`.
