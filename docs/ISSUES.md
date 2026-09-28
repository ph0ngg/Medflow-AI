# ISSUES — Implementation Backlog (MedFlow AI)

Backlog chia theo ưu tiên. Definition of Done: đọc spec + code đúng layer + test pass + build sạch.

## Đã xong (prototype lõi)
- [x] Monorepo + adapter mock + DB models/seed.
- [x] Orchestrator state machine (cũ/mới/red-flag).
- [x] Services: llm/triage/face/stt/tts/ocr.
- [x] API kiosk + admin.
- [x] Frontend React/Vite 15 màn hình.
- [x] pytest 17 tests + docs spec-driven.

## P0 — Cần làm sớm
- [ ] `POST /register-face` (đăng ký khuôn mặt mới) — bản cũ có, chưa port.
- [ ] QR scanner (hiện chỉ CCCD + mã bệnh nhân).
- [ ] Mock "trạng thái máy in" (in phiếu / máy in lỗi fallback).
- [ ] Dashboard admin UI (backend đã có API, frontend admin chưa).

## P1 — Nên có
- [ ] Tích hợp Cohere LLM thật (đã có adapter, cần test e2e với key).
- [ ] STT/TTS e2e với micro/loa kiosk (kiểm thử thiết bị).
- [ ] Wayfinding bản đồ phong phú hơn (hiện là card tĩnh).
- [ ] Biểu mẫu điện tử + cập nhật thông tin cá nhân (Nhóm D).

## P2 — Tương lai
- [ ] Tích hợp HIS/EMR, định danh, BHYT, payment thật (qua adapter).
- [ ] Ký điện tử, tra cứu kết quả.
- [ ] Điều phối đa khoa theo năng lực + queue.
- [ ] Phân tích dữ liệu vận hành kiosk.
