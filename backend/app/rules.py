"""
Clinical safety & business rules — MedFlow AI.

Các quy tắc được tách riêng để:
- Có thể kiểm thử độc lập (testable) theo PRD mục 9.
- Không để LLM tự quyết định toàn bộ logic phân luồng.
- Dễ cấu hình/nâng cấp mà không sửa code nghiệp vụ.

LƯU Ý: Đây là quy tắc prototype. Không phải chuẩn y khoa.
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


def normalize(text: str) -> str:
    """Bỏ dấu tiếng Việt + lowercase + bỏ ký tự đặc biệt để matching robust."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = text.replace("đ", "d")
    # Bỏ dấu câu/đặc biệt (gạch ngang, gạch chéo...) → giữ chữ + số + khoảng trắng
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _word_match(lowered: str, kw: str) -> bool:
    """Khớp keyword theo ranh giới từ (tránh 'ho' khớp nhầm 'hỏi')."""
    return re.search(rf"\b{re.escape(kw)}\b", lowered) is not None


# ── Dấu hiệu cảnh báo (red flag) ────────────────────────
# Rule-based, có thể kiểm thử. Khi khớp → dừng luồng cấp số thông thường.
EMERGENCY_KEYWORDS = [
    "đau ngực", "đau thắt ngực", "khó thở", "thở gấp",
    "vã mồ hôi", "ngất", "bất tỉnh", "hôn mê",
    "co giật", "chảy máu nhiều", "xuất huyết",
    "đau đầu dữ dội", "liệt nửa người", "méo miệng",
    "nói khó", "sốt cao li bì", "khó thở nặng",
]
_EMERGENCY_NORM = [normalize(kw) for kw in EMERGENCY_KEYWORDS]

# ── Ánh xạ triệu chứng → khoa (rule-based) ──────────────
DEPARTMENT_MAPPING: dict[str, list[str]] = {
    "Nội tổng quát": ["mệt mỏi", "sốt nhẹ", "kiểm tra sức khỏe", "khám tổng quát", "đau nhức toàn thân", "chán ăn"],
    "Tim mạch": ["đau ngực", "hồi hộp", "đánh trống ngực", "tức ngực", "cao huyết áp", "tăng huyết áp", "phù chân", "loạn nhịp"],
    "Hô hấp": ["ho", "khó thở", "sổ mũi", "hắt hơi", "đờm", "viêm phổi", "hen suyễn"],
    "Tiêu hóa – Gan mật": ["đau bụng", "buồn nôn", "nôn", "tiêu chảy", "táo bón", "ợ chua", "đầy hơi", "đi ngoài", "vàng da", "đau gan", "sỏi mật"],
    "Nội tiết – Đái tháo đường": ["tiểu nhiều", "khát nước", "sút cân", "mệt mỏi", "bướu cổ", "đường huyết", "tuyến giáp", "tiểu đêm"],
    "Thận – Tiết niệu": ["tiểu buốt", "tiểu rắt", "tiểu máu", "sỏi thận", "phù", "đau vùng thận", "nước tiểu đục"],
    "Cơ xương khớp": ["đau lưng", "đau khớp", "đau cổ", "tê tay", "tê chân", "đau vai", "sưng khớp", "cứng khớp", "đau nhức xương"],
    "Thần kinh": ["đau đầu", "đau nửa đầu", "chóng mặt", "mất ngủ", "run tay", "tê bì chân tay", "động kinh", "suy giảm trí nhớ"],
    "Da liễu": ["ngứa", "nổi mẩn", "phát ban", "mụn", "chàm", "nấm da", "rụng tóc"],
    "Dị ứng – Miễn dịch": ["dị ứng", "dị ứng thuốc", "dị ứng thức ăn", "suy giảm miễn dịch", "mề đay"],
    "Truyền nhiễm / Bệnh nhiệt đới": ["sốt cao", "sốt rét", "sốt xuất huyết", "nhiễm trùng", "sốt kéo dài", "tiêu chảy cấp"],
    "Ung bướu": ["khối u", "u bướu", "sụt cân nhanh", "nổi hạch", "u ở vú"],
    "Ngoại khoa": ["vết thương", "áp xe", "mụn nhọt", "thoát vị", "đau vết mổ", "nhiễm trùng vết thương"],
    "Ngoại tiêu hóa": ["viêm ruột thừa", "đau bụng cấp", "trĩ", "đau hậu môn", "thoát vị bẹn"],
    "Ngoại tiết niệu – Nam học": ["phì đại tuyến tiền liệt", "tiểu khó", "yếu sinh lý", "sỏi tiết niệu", "bao quy đầu"],
    "Chấn thương chỉnh hình – Y học thể thao": ["gãy xương", "bong gân", "trật khớp", "chấn thương", "đau cơ sau tập", "giãn dây chằng"],
    "Tai Mũi Họng": ["đau tai", "ù tai", "viêm mũi", "viêm họng", "nghẹt mũi", "chảy máu cam", "đau họng", "viêm amidan"],
    "Mắt": ["mờ mắt", "đau mắt", "đỏ mắt", "chảy nước mắt", "nhìn đôi", "khô mắt", "cộm mắt"],
    "Răng Hàm Mặt": ["đau răng", "sâu răng", "viêm lợi", "chảy máu chân răng", "đau hàm", "mọc răng khôn"],
    "Sản – Phụ khoa": ["kinh nguyệt", "đau bụng kinh", "khí hư", "khám thai", "phụ khoa", "thai kỳ"],
    "Nhi khoa": ["trẻ em", "trẻ sốt", "trẻ ho", "trẻ tiêu chảy", "trẻ biếng ăn", "khám trẻ"],
    "Sức khỏe tâm thần": ["trầm cảm", "lo âu", "căng thẳng", "stress", "hoang tưởng", "mất ngủ kéo dài"],
    "Phục hồi chức năng": ["phục hồi chức năng", "vật lý trị liệu", "tai biến", "cứng khớp sau chấn thương", "bại liệt"],
    "Y học cổ truyền": ["châm cứu", "bấm huyệt", "xoa bóp", "thuốc nam"],
    "Cấp cứu – Hồi sức tích cực": [],
}
_DEPARTMENT_NORM = {
    dept: [normalize(kw) for kw in kws]
    for dept, kws in DEPARTMENT_MAPPING.items()
}
# ── Intent (ý định) rule-based — dùng để fallback khi LLM lỗi ──
INTENT_KEYWORDS: dict[str, list[str]] = {
    "check_in": ["lịch hẹn", "check-in", "check in", "đến khám theo hẹn", "có hẹn"],
    "follow_up": ["khám lại", "tái khám", "khám lại theo hẹn", "tái khám theo đơn"],
    "new_visit": ["đau", "ho", "sốt", "mệt", "khám bệnh", "khám mới", "triệu chứng"],
    "payment": ["thanh toán", "đóng tiền", "đóng phí", "viện phí"],
    "lookup": ["tra cứu", "kết quả", "xem lịch hẹn", "số thứ tự"],
    "support": ["giúp đỡ", "hỗ trợ", "nhân viên", "không biết"],
}
_INTENT_NORM = {
    intent: [normalize(kw) for kw in kws]
    for intent, kws in INTENT_KEYWORDS.items()
}

# ── Confirmation keywords (xác nhận của bệnh nhân) ──────
CONFIRM_YES = ["có", "đồng ý", "ok", "được", "vâng", "dạ", "xác nhận", "chấp nhận", "yes", "đăng ký", "làm"]
CONFIRM_NO = ["không", "không muốn", "chọn khoa khác", "khoa khác", "sai", "đổi", "khác", "no"]
_CONFIRM_YES_NORM = [normalize(kw) for kw in CONFIRM_YES]
_CONFIRM_NO_NORM = [normalize(kw) for kw in CONFIRM_NO]

# ── Fee (đồng) prototype cho mỗi lượt khám ─────────────
REGISTRATION_FEE = 200_000
INSURANCE_COVERAGE_PERCENT = 80  # BHYT chi trả 80% (mô phỏng)


@dataclass
class DepartmentSuggestion:
    """Kết quả đề xuất khoa (combine LLM + rules)."""
    department: str
    reason: str
    source: str          # "llm" | "rules" | "hybrid"
    confidence: float    # 0..1


def check_emergency(text: str) -> bool:
    """Kiểm tra dấu hiệu cảnh báo theo rule (bỏ dấu, case-insensitive)."""
    lowered = normalize(text)
    return any(_word_match(lowered, kw) for kw in _EMERGENCY_NORM)


def suggest_department_by_rules(text: str) -> Optional[DepartmentSuggestion]:
    """Đề xuất khoa dựa trên keyword matching thuần túy."""
    lowered = normalize(text)
    best: tuple[str, int] | None = None
    for dept, keywords in _DEPARTMENT_NORM.items():
        score = sum(1 for kw in keywords if _word_match(lowered, kw))
        if score and (best is None or score > best[1]):
            best = (dept, score)
    if not best:
        return None
    dept, score = best
    total_possible = len(_DEPARTMENT_NORM[dept])
    confidence = min(0.95, 0.4 + 0.5 * (score / max(1, total_possible)))
    return DepartmentSuggestion(dept, f"Khớp {score} triệu chứng với chuyên khoa", "rules", confidence)


def detect_intent_by_rules(text: str) -> Optional[str]:
    """Phát hiện intent bằng keyword rule (fallback cho LLM)."""
    lowered = normalize(text)
    for intent, keywords in _INTENT_NORM.items():
        if any(_word_match(lowered, kw) for kw in keywords):
            return intent
    return None


def is_confirmation_yes(text: str) -> bool:
    lowered = normalize(text).strip()
    # Tránh nhầm "không" nằm trong câu "không đau"
    for no_kw in _CONFIRM_NO_NORM:
        if lowered == no_kw or lowered.startswith(no_kw + " "):
            return False
    return any(_word_match(lowered, kw) for kw in _CONFIRM_YES_NORM)


def is_confirmation_no(text: str) -> bool:
    lowered = normalize(text).strip()
    return any(_word_match(lowered, kw) for kw in _CONFIRM_NO_NORM)
