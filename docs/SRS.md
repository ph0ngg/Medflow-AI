# SRS — Functional Specification (MedFlow AI)

Mô tả chức năng, input/output, trạng thái, lỗi và acceptance criteria.

## FR-1. Phát hiện & nhận diện khuôn mặt
- **Input**: ảnh frame (JPEG) từ camera.
- **Output**: `{ detected, faces: [{id, name, bbox}], available }`.
- **Lỗi**: camera không hoạt động → `detected=false`, frontend chuyển sang CCCD.
- **AC**: nhận diện bệnh nhân cũ khi có embedding khớp; người lạ → `name=null`.

## FR-2. Xác thực CCCD / mã bệnh nhân
- **Input**: `cccd` (12 số) hoặc `code` (mã bệnh nhân).
- **Output**: session + `profile` (tên, dob, cccd, BHYT, lịch hẹn, lịch sử).
- **Lỗi**: CCCD sai định dạng → `invalid_cccd`; mã không tồn tại → `patient_not_found`.
- **AC**: bệnh nhân cũ → `is_returning=true`; bệnh nhân mới → tạo hồ sơ mới.

## FR-3. Hội thoại nhiều lượt
- **Input**: `session_id`, `message` (text) hoặc `audio` (voice).
- **Output**: `{ intent, state, response, symptoms, suggested_department?, queue_info?, payment?, ticket? }`.
- **AC**: duy trì context trong session; hỏi bổ sung khi thiếu thông tin; chuyển state đúng.

## FR-4. Phân luồng (đề xuất khoa)
- Kết hợp LLM suggestion + rule engine (`app/rules.py`).
- **AC**: `suggested_department` hợp lệ trong danh sách khoa; kèm `queue_info`.

## FR-5. Red-flag
- **AC**: khi khớp rule → `state=emergency`, `action=alert_staff`, KHÔNG cấp số.

## FR-6. Hàng đợi & cấp số
- **AC**: hiển thị `current_queue`, `estimated_wait`; chỉ cấp số sau khi bệnh nhân xác nhận (`/confirm`).

## FR-7. Thanh toán (mock)
- **AC**: bệnh nhân có BHYT hợp lệ → BHYT chi trả 80%; ngược lại trả 100%.

## FR-8. Session & privacy
- **AC**: `end-session` xóa session; frontend tự reset sau timeout; không hiển thị PII trước xác thực.

## FR-9. Admin dashboard
- **AC**: `stats`, `patients`, `departments`, `queue`, `payments`, `conversations` trả JSON.

## Non-functional
- Backend khởi động được khi thiếu model nặng (ONNX/CV2) — service degrade an toàn.
- Rule matching chịu được tiếng Việt không dấu.
