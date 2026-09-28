"""
Test Orchestrator — luồng chính theo PRD mục 6 + tiêu chí nghiệm thu mục 13.
"""
from app.orchestrator import KioskOrchestrator
from app.session import SessionState


def _o():
    return KioskOrchestrator()


def test_new_patient_full_flow():
    o = _o()
    s = o.start_session()
    assert s.state == SessionState.IDENTIFYING

    r = o.verify_cccd(s.session_id, "001078000003")
    assert r["state"] == "profile_review"
    assert r["profile"]["full_name"] == "Lê Văn C"
    assert r["profile"]["insurance_valid"] is False

    r = o.process_message(s.session_id, "tôi bị đau bụng")
    assert r["state"] == "triaging"
    assert r["suggested_department"] == "Tiêu hóa – Gan mật"
    assert r["queue_info"]["current_queue"] > 0

    # Xác nhận đăng ký → bệnh nhân mới không BHYT → phải thanh toán
    r = o.process_message(s.session_id, "có")
    assert r["state"] == "payment"
    assert r["payment"]["patient_pay"] > 0

    r = o.process_message(s.session_id, "có")
    assert r["state"] == "confirming"

    r = o.confirm_and_issue(s.session_id)
    assert r["state"] == "done"
    assert r["ticket"]["ticket_number"] > 0
    assert r["ticket"]["department"] == "Tiêu hóa – Gan mật"


def test_returning_patient_check_in_flow():
    o = _o()
    s = o.start_session("Nguyễn Văn A", "1")
    assert s.is_returning is True
    assert s.state == SessionState.GREETING

    r = o.process_message(s.session_id, "tôi có lịch hẹn")
    assert r["state"] == "triaging"
    assert r["suggested_department"] == "Nội tiết – Đái tháo đường"


def test_face_recognition_does_not_go_back_to_cccd():
    """Nhận diện mặt thành công (tên không khớp DB) vẫn phải link bệnh nhân,
    KHÔNG đẩy người dùng quay lại bước nhập CCCD."""
    o = _o()
    s = o.start_session("Tung", "1")  # tên FAISS không có trong seed patients
    assert s.is_returning is True
    assert s.patient_id is not None  # tự tạo/link hồ sơ

    r = o.process_message(s.session_id, "tôi bị đau bụng")
    assert r["state"] == "triaging"
    assert r["suggested_department"] == "Tiêu hóa – Gan mật"


def test_manual_department_selection_full_flow():
    """Tự chọn phòng khám (kiosk truyền thống) → vẫn cấp số được."""
    o = _o()
    s = o.start_session()

    r = o.select_department(s.session_id, "Da liễu")
    assert r["state"] == "triaging"
    assert r["suggested_department"] == "Da liễu"

    r = o.process_message(s.session_id, "có")
    assert r["state"] == "payment"

    r = o.process_message(s.session_id, "có")
    assert r["state"] == "confirming"

    r = o.confirm_and_issue(s.session_id)
    assert r["state"] == "done"
    assert r["ticket"]["department"] == "Da liễu"


def test_emergency_flow_no_ticket():
    o = _o()
    s = o.start_session()
    r = o.process_message(s.session_id, "tôi bị đau ngực dữ dội")
    assert r["state"] == "emergency"
    assert r["action"] == "alert_staff"

    # Không thể cấp số khi đang emergency
    r2 = o.confirm_and_issue(s.session_id)
    assert "error" in r2 or r2.get("state") != "done"


def test_unknown_symptom_asks_more():
    o = _o()
    s = o.start_session()
    o.verify_cccd(s.session_id, "001078000003")
    r = o.process_message(s.session_id, "xin chào")
    assert r["state"] == "collecting"


def test_session_end_removes_session():
    o = _o()
    s = o.start_session()
    o.end_session(s.session_id)
    assert o.get_session(s.session_id) is None


def test_llm_department_has_priority_over_rules(monkeypatch):
    """LLM đề xuất khoa → được ưu tiên hơn rule (PRD: LLM quyết định nhiều hơn)."""
    from app.orchestrator import llm_service as orch_llm
    o = _o()
    s = o.start_session()
    o.verify_cccd(s.session_id, "001078000003")

    monkeypatch.setattr(orch_llm, "chat", lambda *a, **k: {
        "intent": "new_visit",
        "symptoms": ["đau bụng"],
        "response": "ok",
        "need_more_info": False,
        "suggested_department": "Mắt",  # khác với rule (đau bụng → Tiêu hóa – Gan mật)
    })

    r = o.process_message(s.session_id, "tôi bị đau bụng")
    assert r["state"] == "triaging"
    assert r["suggested_department"] == "Mắt"


def test_llm_need_more_info_not_overridden_by_rules(monkeypatch):
    """LLM muốn hỏi thêm → rule KHÔNG được ép đề xuất khoa."""
    from app.orchestrator import llm_service as orch_llm
    o = _o()
    s = o.start_session()
    o.verify_cccd(s.session_id, "001078000003")

    monkeypatch.setattr(orch_llm, "chat", lambda *a, **k: {
        "intent": "new_visit",
        "symptoms": ["đau bụng"],
        "response": "Anh/chị đau bao lâu rồi?",
        "need_more_info": True,
        "suggested_department": None,
    })

    r = o.process_message(s.session_id, "tôi bị đau bụng")
    assert r["state"] == "collecting"
