"""
Test API — kiểm thử endpoint qua FastAPI TestClient.
"""
from fastapi.testclient import TestClient

from app.main import app


def _client():
    return TestClient(app)


def test_health():
    with _client() as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_departments():
    with _client() as c:
        r = c.get("/api/kiosk/departments")
        assert r.status_code == 200
        depts = r.json()
        assert len(depts) >= 10
        assert any(d["name"] == "Tiêu hóa – Gan mật" for d in depts)
        assert any(d["name"] == "Thần kinh" for d in depts)


def test_full_kiosk_flow_via_api():
    with _client() as c:
        # 1. start session (bệnh nhân mới)
        r = c.post("/api/kiosk/start-session", data={})
        assert r.status_code == 200
        sid = r.json()["session_id"]
        assert r.json()["state"] == "identifying"

        # 2. verify CCCD
        r = c.post("/api/kiosk/verify-cccd", data={"session_id": sid, "cccd": "001078000003"})
        assert r.status_code == 200
        assert r.json()["state"] == "profile_review"

        # 3. gửi triệu chứng
        r = c.post("/api/kiosk/message", json={"session_id": sid, "message": "tôi bị đau bụng"})
        assert r.json()["state"] == "triaging"

        # 4. xác nhận → payment (không BHYT)
        r = c.post("/api/kiosk/message", json={"session_id": sid, "message": "có"})
        assert r.json()["state"] == "payment"

        # 5. thanh toán
        r = c.post("/api/kiosk/pay", data={"session_id": sid, "method": "mock"})
        assert r.json()["state"] == "confirming"

        # 6. xác nhận cấp số
        r = c.post("/api/kiosk/confirm", json={"session_id": sid})
        body = r.json()
        assert body["state"] == "done"
        assert body["ticket"]["ticket_number"] > 0


def test_admin_stats():
    with _client() as c:
        r = c.get("/api/admin/stats")
        assert r.status_code == 200
        body = r.json()
        assert "patients" in body
        assert body["patients"] >= 3


def test_invalid_cccd():
    with _client() as c:
        r = c.post("/api/kiosk/start-session", data={})
        sid = r.json()["session_id"]
        r = c.post("/api/kiosk/verify-cccd", data={"session_id": sid, "cccd": "abc"})
        assert r.json().get("error") == "invalid_cccd"


def test_register_new_patient():
    with _client() as c:
        r = c.post("/api/kiosk/register", data={
            "full_name": "Phạm Văn D", "dob": "01/01/2000",
            "address": "Hải Phòng", "phone": "0901000004",
            "cccd": "001100000004",
        })
        body = r.json()
        assert body.get("patient_name") == "Phạm Văn D"
        assert body.get("state") == "greeting"
        assert body["profile"]["full_name"] == "Phạm Văn D"
        assert body["profile"]["address"] == "Hải Phòng"
        assert body["session_id"]


def test_register_missing_required():
    with _client() as c:
        r = c.post("/api/kiosk/register", data={"full_name": "", "dob": ""})
        assert r.json().get("error") == "missing_fullname"


def test_register_duplicate_cccd():
    with _client() as c:
        r = c.post("/api/kiosk/register", data={
            "full_name": "Người Khác", "dob": "01/01/1990", "cccd": "001085000001",
        })
        assert r.json().get("error") == "cccd_exists"
