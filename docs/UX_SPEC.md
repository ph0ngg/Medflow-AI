# UX SPEC — Màn hình + interaction + states

Ánh xạ 15 màn hình PRD → implementation (`frontend/src/screens/`).

| # | Màn hình | File | Nội dung chính |
|---|---|---|---|
| 01 | Màn hình chờ | `IdleScreen` | Logo, "Nói với tôi điều anh/chị cần", fallback buttons, camera |
| 02 | Phát hiện người dùng | `IdleScreen` (CameraFeed) | Nhận biết người, hướng dẫn nhìn camera |
| 03 | Xác thực danh tính | `AuthScreen` | CCCD (quét/nhập) hoặc mã bệnh nhân |
| 04 | Hồ sơ bệnh nhân | `ProfileScreen` | Tên, dob, CCCD (mask), BHYT, lịch hẹn |
| 05 | Lịch hẹn | `ProfileScreen` (list) | DS lịch hẹn + trạng thái |
| 06 | Hội thoại AI | `ChatScreen` | Transcript, voice button, text input |
| 07 | Tóm tắt nhu cầu | `DepartmentScreen` (summary) | Thông tin AI đã hiểu |
| 08 | Đề xuất khoa | `DepartmentScreen` | Khoa + lý do + disclaimer |
| 09 | Hàng đợi | `DepartmentScreen` (QueueInfoCard) | Số chờ + thời gian chờ |
| 10 | Thanh toán | `PaymentScreen` | Phí, BHYT chi trả, cần trả |
| 11 | Xác nhận đăng ký | `ConfirmScreen` | Tóm tắt + nút xác nhận |
| 12 | Cấp số | `TicketScreen` | Số thứ tự lớn + in phiếu |
| 13 | Wayfinding | `TicketScreen` (WayfindingCard) | Tầng/phòng + hướng dẫn |
| 14 | Cảnh báo | `EmergencyScreen` | Red-flag, liên hệ nhân viên y tế |
| 15 | Kết thúc | `EndScreen` | Hoàn tất + phiên mới |

## Nguyên tắc UX (PRD mục 8)
- Voice-first; touch là fallback.
- Một hành động chính mỗi màn hình.
- Luôn hiển thị trạng thái (đang nghe/xử lý/...).
- Chữ lớn, tương phản cao (xem `DESIGN_SYSTEM.md`).
- Không thuật ngữ y khoa khó hiểu.
- Xác nhận trước hành động quan trọng.
- Không hiển thị PII trước xác thực (mask CCCD/BHYT).
- Luôn có đường thoát (quay lại / gọi nhân viên).
- Reset phiên sau khi kết thúc (auto 25s).

## Interaction states
`busy` (spinner), `recording` (mic), camera error, backend error → hiển thị thân thiện.
