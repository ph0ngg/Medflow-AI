# ADR-0002: SQLite prototype + mock adapters

- **Trạng thái**: Accepted
- **Ngày**: 2026-08-30

## Bối cảnh
Prototype không có HIS/EMR/BHYT/queue/payment thật.

## Quyết định
- Data store: SQLite (SQLAlchemy).
- Mọi integration thật qua `backend/app/adapters/` (interface + mock).
- `MEDFLOW_INTEGRATION_MODE=mock` chọn mock; khi có integration thật, thêm adapter.

## Lý do
PRD mục 11: "Các integration thật phải được tách qua adapter/interface để prototype có thể
dùng mock service mà không thay đổi business logic."

## Hệ quả
- Business logic (orchestrator/services) không gọi trực tiếp API ngoài.
- Mock adapters đọc/ghi chính database prototype (mô phỏng hệ thống ngoài).
