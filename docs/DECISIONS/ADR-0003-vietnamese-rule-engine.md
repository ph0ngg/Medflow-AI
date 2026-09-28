# ADR-0003: Rule engine tiếng Việt không dấu

- **Trạng thái**: Accepted
- **Ngày**: 2026-08-30

## Bối cảnh
STT tiếng Việt có thể trả văn bản có dấu; người dùng gõ tay thường không dấu.
Keyword matching dạng substring gây false positive ("ho" khớp "hỏi").

## Quyết định
- `app/rules.py` cung cấp `normalize()` bỏ dấu tiếng Việt.
- Mọi matching (red-flag, dept, intent, confirm) dùng **word-boundary regex** trên văn bản đã chuẩn hóa.

## Hệ quả
- Chịu được "dau bung" lẫn "đau bụng".
- Tránh khớp nhầm substring. Test: `test_suggest_department_no_match`, `test_normalize_vietnamese`.
