# USER FLOWS — State Machine (MedFlow AI)

## State machine phiên (backend `session.py`)

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> identifying: phát hiện người lạ / chạm đăng ký
    idle --> greeting: nhận diện mặt (bệnh nhân cũ)
    identifying --> profile_review: CCCD/mã hợp lệ
    profile_review --> greeting: bệnh nhân cũ
    profile_review --> collecting: bệnh nhân mới xác nhận
    greeting --> collecting: nói nhu cầu (new_visit)
    greeting --> triaging: check_in / follow_up có dữ liệu
    collecting --> triaging: đủ thông tin → đề xuất khoa
    collecting --> collecting: hỏi bổ sung
    triaging --> payment: xác nhận "có" (có phí)
    triaging --> confirming: xác nhận "có" (hết phí / BHYT)
    payment --> confirming: thanh toán xong
    confirming --> done: xác nhận cấp số
    triaging --> emergency: red-flag
    collecting --> emergency: red-flag
    done --> [*]: kết thúc / timeout
    emergency --> [*]: đã hiểu / reset
```

## Luồng bệnh nhân cũ
Phát hiện → nhận diện mặt → chào + hồ sơ → (check-in | tái khám | triệu chứng mới) → đề xuất → queue → xác nhận → cấp số.

## Luồng bệnh nhân mới
Phát hiện → CCCD → hồ sơ (BHYT) → AI hỏi triệu chứng → đề xuất → queue → thanh toán (nếu có) → xác nhận → cấp số.

## Luồng cảnh báo (red-flag)
Phát hiện dấu hiệu → dừng luồng → hiển thị cảnh báo → hướng dẫn gặp nhân viên y tế → ghi nhận sự kiện.
