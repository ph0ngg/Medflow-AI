# PRD — MedFlow AI (v2.0)

> Bản đầy đủ nằm tại `MedFlow_AI_PRD_v2.txt` (gốc). File này tóm tắt để coding agent có nguồn ngữ cảnh ổn định.

## 1. Sản phẩm
MedFlow AI là **kiosk AI hội thoại** tự động hóa tiếp đón, xác thực danh tính, khai thác nhu cầu,
phân luồng và điều phối bệnh nhân. Người bệnh **nói nhu cầu bằng ngôn ngữ đời thường** thay vì tự tìm chức năng.

Hai lớp: (1) lõi kiosk bệnh viện (xác thực, check-in/đăng ký, hàng đợi, thanh toán, hướng dẫn);
(2) lớp AI hội thoại (trợ lý tiếp đón & điều phối).

Prototype chứng minh hành trình hoàn chỉnh; **không** thay thế HIS/EMR, **không** chẩn đoán/điều trị.

## 2. Mục tiêu
- Tiếp đón tự động bằng voice-first.
- Xác thực: khuôn mặt + dự phòng (CCCD/QR/mã bệnh nhân).
- Cá nhân hóa bằng dữ liệu được phép (định danh, BHYT, lịch hẹn, lịch sử khám).
- Đăng ký khám, check-in, tái khám, cấp số.
- AI khai thác triệu chứng → đề xuất khoa (không chẩn đoán).
- Kiểm tra hàng đợi, thanh toán, hướng dẫn vị trí.
- Nền tảng tích hợp được HIS/EMR/BHYT qua adapter.

## 3. Phạm vi chức năng
- **A. Tiếp đón & xác thực**: phát hiện người, nhận diện mặt, quét CCCD/QR/mã, cũ/mới, xác nhận hồ sơ + BHYT, check-in, đăng ký mới, tái khám.
- **B. AI tiếp nhận & phân luồng**: voice + STT, nhận diện intent, hội thoại nhiều lượt, khai thác triệu chứng, dùng lịch sử/lịch hẹn, đề xuất khoa, phát hiện red-flag, handoff nhân viên.
- **C. Điều phối**: kiểm tra queue, số chờ + thời gian chờ, xác nhận trước khi cấp số, cấp số, in phiếu, wayfinding.
- **D. Dịch vụ mở rộng**: cập nhật thông tin, biểu mẫu, ký điện tử, thanh toán, in chứng từ, tra cứu.
- **E. Hỗ trợ & ngoại lệ**: fallback khi không nhận diện/không đọc CCCD/AI không hiểu/không đủ dữ liệu/red-flag/mất backend/không máy in.

## 4. Phạm vi prototype (Must-have)
Home → xác thực → hồ sơ → hội thoại → đề xuất khoa → queue → xác nhận → ticket.
Face recognition (hoặc mô phỏng), CCCD scanner (hoặc mock), STT tiếng Việt, hội thoại nhiều lượt,
rule-based recommendation + AI extraction, khoa mẫu, queue mock realtime, in ticket (mock),
red-flag flow, fallback touch.

Should-have: lịch hẹn, BHYT mock, thanh toán mock, wayfinding đơn giản, dashboard admin cơ bản, TTS.

## 5. Tiêu chí nghiệm thu (rút gọn)
Xem `docs/TEST_SPEC.md` — bệnh nhân cũ/mới xác thực được; nói tiếng Việt → text; hội thoại nhiều lượt;
đề xuất khoa theo rule; không tự nhận chẩn đoán; red-flag không cấp số; queue hiển thị; xác nhận trước khi cấp số;
ticket hiển thị/in; fallback khi AI/camera/scanner/in lỗi; reset phiên sau khi kết thúc.

## 6. Ngoài phạm vi
Chẩn đoán/kê đơn/điều trị, quản lý toàn bộ EMR, tích hợp production khi chưa có phân quyền,
xây HIS, tự động quyết định y khoa không có human oversight.
