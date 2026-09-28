# TEST SPEC — Test cases & golden scenarios

Nguồn: `tests/` (17 tests). Chạy: `python -m pytest tests -v`.

## 1. Rules (`test_rules.py`)
- `test_normalize_vietnamese`: "Đau Bụng" → "dau bung".
- `test_check_emergency_*`: red-flag có dấu & không dấu.
- `test_suggest_department`: "đau bụng + buồn nôn" → Nội tiêu hóa.
- `test_suggest_department_no_match`: không khớp → None (tránh "ho" khớp nhầm "hỏi").
- `test_detect_intent`: check_in / follow_up / new_visit / payment.
- `test_confirmation`: có/đồng ý/không; "không đau nữa" KHÔNG phải "không".

## 2. Orchestrator (`test_orchestrator.py`)
- `test_new_patient_full_flow`: CCCD mới → đau bụng → triaging → payment → confirming → done + ticket.
- `test_returning_patient_check_in_flow`: nhận diện A → "có lịch hẹn" → triaging Nội tiết.
- `test_emergency_flow_no_ticket`: đau ngực → emergency, không cấp số.
- `test_unknown_symptom_asks_more`: "xin chào" → collecting.
- `test_session_end_removes_session`.

## 3. API (`test_api.py`)
- health, departments, full kiosk flow qua HTTP, admin stats, invalid cccd.

## Golden conversation (bệnh nhân mới)
```
Kiosk: "Vui lòng quét CCCD hoặc nhập mã bệnh nhân."
BN:    [quét CCCD 001078000003]
Kiosk: hồ sơ Lê Văn C
BN:    "tôi bị đau bụng"
Kiosk: đề xuất Nội tiêu hóa + queue + "xác nhận chứ?"
BN:    "có"
Kiosk: thanh toán 200.000đ (không BHYT)
BN:    "có"
Kiosk: xác nhận cuối
BN:    [xác nhận] → cấp số + wayfinding
```

## Golden conversation (red-flag)
```
BN: "tôi bị đau ngực dữ dội"
Kiosk: CẢNH BÁO — liên hệ nhân viên y tế ngay. KHÔNG cấp số.
```

## Acceptance criteria (PRD mục 13)
Được map 1-1 với các test trên; thêm tiêu chí "phiên reset sau kết thúc" (test_session_end).
