"""
Test rules — clinical safety & business rules (PRD mục 9: rule có thể kiểm thử).
"""
from app.rules import (
    check_emergency,
    suggest_department_by_rules,
    detect_intent_by_rules,
    is_confirmation_yes,
    is_confirmation_no,
    normalize,
)


def test_normalize_vietnamese():
    assert normalize("Đau Bụng") == "dau bung"
    assert normalize("đau bụng") == "dau bung"
    assert normalize("ĐAU NGỰC") == "dau nguc"


def test_check_emergency_with_diacritics():
    assert check_emergency("tôi bị đau ngực dữ dội") is True
    assert check_emergency("khó thở nặng") is True


def test_check_emergency_without_diacritics():
    assert check_emergency("toi bi dau nguc") is True
    assert check_emergency("toi bi dau bung") is False


def test_suggest_department():
    s = suggest_department_by_rules("tôi bị đau bụng và buồn nôn")
    assert s is not None
    assert s.department == "Tiêu hóa – Gan mật"
    assert s.source == "rules"


def test_suggest_department_no_match():
    assert suggest_department_by_rules("tôi muốn hỏi về thủ tục") is None


def test_detect_intent():
    assert detect_intent_by_rules("tôi có lịch hẹn khám") == "check_in"
    assert detect_intent_by_rules("tôi muốn tái khám") == "follow_up"
    assert detect_intent_by_rules("tôi bị ho và sốt") == "new_visit"
    assert detect_intent_by_rules("tôi muốn thanh toán viện phí") == "payment"


def test_confirmation():
    assert is_confirmation_yes("có") is True
    assert is_confirmation_yes("đồng ý") is True
    assert is_confirmation_no("không") is True
    assert is_confirmation_no("chọn khoa khác") is True
    # Tránh nhầm "không" trong câu phủ định
    assert is_confirmation_yes("không đau nữa") is False
