# AI SPEC — Intents + Dialogue + Rules + Safety

## Intent (ý định)
`check_in`, `new_visit`, `follow_up`, `payment`, `lookup`, `support`, `emergency`.

Nguồn xác định intent: LLM (cohere/openai/mock) → fallback `rules.detect_intent_by_rules`.

## Dialogue states (backend `session.py`)
`idle → identifying → profile_review → greeting/collecting → triaging → payment → confirming → done`
+ nhánh `emergency`.

## Rules (backend `app/rules.py`) — phải testable
- `check_emergency(text)`: red-flag keywords (đau ngực, khó thở, bất tỉnh, co giật...).
- `suggest_department_by_rules(text)`: keyword mapping triệu chứng → khoa.
- `detect_intent_by_rules(text)`: intent keyword.
- `is_confirmation_yes/no(text)`: xác nhận của bệnh nhân.
- `normalize(text)`: bỏ dấu tiếng Việt (matching chịu được "dau bung" lẫn "đau bụng").

## Kết hợp LLM + rules (đề xuất khoa)
1. LLM trả `suggested_department` (nếu có).
2. `triage.suggest_department`: nếu LLM đề xuất khoa **hợp lệ** → hybrid; ngược lại dùng rule.
3. Không bao giờ để LLM tự quyết định khoa ngoài danh sách khoa hợp lệ.

## Safety (PRD mục 9)
- AI không chẩn đoán/kê đơn/điều trị.
- Red-flag → dừng luồng cấp số, `action=alert_staff`.
- Confidence thấp/thiếu dữ liệu → hỏi thêm hoặc chuyển nhân viên.
- Hành động quan trọng (cấp số, thanh toán) phải có bước xác nhận.
- Không log PII; conversation lưu tóm tắt (không cần thiết lưu PII).

## Prompt hệ thống (LLM)
Xem `backend/app/services/llm_service.py` — yêu cầu trả JSON `{intent, symptoms, response, need_more_info, suggested_department}`.
