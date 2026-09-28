# API SPEC — MedFlow AI

Base URL: `http://localhost:8080`. OpenAPI tự động tại `/docs`.

## Kiosk (`/api/kiosk`)
| Method | Path | Body | Mô tả |
|---|---|---|---|
| POST | `/detect-face` | `image` (file) | Phát hiện/nhận diện mặt từ frame |
| POST | `/start-session` | form `face_name?`, `face_id?` | Bắt đầu phiên (cũ/mới) |
| POST | `/scan-cccd` | `image` (file) | OCR trích xuất thông tin CCCD |
| POST | `/verify-cccd` | form `session_id`, `cccd?`/`code?` | Xác thực & gắn danh tính |
| GET | `/session/{id}` | — | Lấy trạng thái phiên |
| POST | `/message` | JSON `{session_id, message}` | Gửi text hội thoại |
| POST | `/voice-message` | form `session_id`, `audio` | Voice → STT → LLM |
| POST | `/tts` | JSON `{session_id, message}` | Text → audio (mp3) |
| POST | `/select-department` | form `session_id`, `department` | Chọn khoa (fallback) |
| POST | `/pay` | form `session_id`, `method?` | Xử lý thanh toán (mock) |
| POST | `/confirm` | JSON `{session_id}` | Xác nhận & cấp số |
| POST | `/end-session` | JSON `{session_id}` | Kết thúc phiên |
| GET | `/departments` | — | Danh sách khoa + queue |
| GET | `/queue/{department}` | — | Queue của 1 khoa |

## Response chung (hội thoại)
```json
{
  "intent": "check_in|new_visit|follow_up|payment|lookup|support|emergency|issued",
  "state": "idle|identifying|profile_review|greeting|collecting|triaging|payment|confirming|done|emergency",
  "response": "...",
  "suggested_department": "...", "queue_info": {...}, "payment": {...}, "ticket": {...}
}
```

## Admin (`/api/admin`)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/stats` | Tổng quan (patients, departments, tickets, payments) |
| GET/POST | `/patients` | DS / thêm bệnh nhân |
| GET | `/departments` | DS khoa + queue |
| PUT | `/departments/{id}` | Cấu hình queue |
| GET | `/queue` | DS số thứ tự |
| GET | `/payments` | DS thanh toán |
| GET | `/conversations` | DS hội thoại (tóm tắt, không PII) |

## Error codes
- `400`: `invalid_cccd`, `patient_not_found`, `invalid_image`, `STT failed`
- `404`: `Session not found`
- `500`: `TTS failed`
