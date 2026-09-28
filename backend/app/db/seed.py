"""
Seed data — MedFlow AI (prototype).

Dữ liệu mẫu theo PRD mục 10.1. Chỉ dùng cho demo/prototype,
KHÔNG phải dữ liệu bệnh nhân thật.
"""
from app.db.models import (
    SessionLocal, Patient, Insurance, Appointment, VisitHistory, Department,
)

DEPARTMENTS = [
    {"name": "Nội tổng quát", "location": "Tầng 1 - P.101", "services": "Khám tổng quát, sức khỏe định kỳ", "current_queue": 6, "estimated_wait": 15},
    {"name": "Tim mạch", "location": "Tầng 2 - P.201", "services": "Khám tim mạch, huyết áp", "current_queue": 5, "estimated_wait": 15},
    {"name": "Hô hấp", "location": "Tầng 2 - P.205", "services": "Khám hô hấp, phổi", "current_queue": 3, "estimated_wait": 10},
    {"name": "Tiêu hóa – Gan mật", "location": "Tầng 2 - P.210", "services": "Bệnh lý tiêu hóa, gan, mật", "current_queue": 8, "estimated_wait": 20},
    {"name": "Nội tiết – Đái tháo đường", "location": "Tầng 3 - P.301", "services": "Đái tháo đường, tuyến giáp", "current_queue": 12, "estimated_wait": 30},
    {"name": "Thận – Tiết niệu", "location": "Tầng 3 - P.305", "services": "Bệnh thận, tiết niệu", "current_queue": 4, "estimated_wait": 12},
    {"name": "Cơ xương khớp", "location": "Tầng 3 - P.310", "services": "Khớp, cột sống, cơ xương", "current_queue": 7, "estimated_wait": 18},
    {"name": "Thần kinh", "location": "Tầng 4 - P.401", "services": "Thần kinh, đau đầu", "current_queue": 9, "estimated_wait": 22},
    {"name": "Da liễu", "location": "Tầng 4 - P.405", "services": "Bệnh da", "current_queue": 2, "estimated_wait": 5},
    {"name": "Dị ứng – Miễn dịch", "location": "Tầng 4 - P.410", "services": "Dị ứng, miễn dịch", "current_queue": 3, "estimated_wait": 8},
    {"name": "Truyền nhiễm / Bệnh nhiệt đới", "location": "Tầng 5 - P.501", "services": "Sốt xuất huyết, bệnh truyền nhiễm", "current_queue": 4, "estimated_wait": 10},
    {"name": "Ung bướu", "location": "Tầng 5 - P.505", "services": "Khám và điều trị ung bướu", "current_queue": 5, "estimated_wait": 14},
    {"name": "Ngoại khoa", "location": "Tầng 5 - P.510", "services": "Ngoại khoa tổng quát", "current_queue": 6, "estimated_wait": 16},
    {"name": "Ngoại tiêu hóa", "location": "Tầng 6 - P.601", "services": "Ngoại khoa tiêu hóa", "current_queue": 3, "estimated_wait": 9},
    {"name": "Ngoại tiết niệu – Nam học", "location": "Tầng 6 - P.605", "services": "Ngoại tiết niệu, nam khoa", "current_queue": 3, "estimated_wait": 9},
    {"name": "Chấn thương chỉnh hình – Y học thể thao", "location": "Tầng 6 - P.610", "services": "Chấn thương, chỉnh hình, thể thao", "current_queue": 5, "estimated_wait": 14},
    {"name": "Tai Mũi Họng", "location": "Tầng 7 - P.701", "services": "Tai, mũi, họng", "current_queue": 10, "estimated_wait": 25},
    {"name": "Mắt", "location": "Tầng 7 - P.705", "services": "Khám mắt, khúc xạ", "current_queue": 4, "estimated_wait": 12},
    {"name": "Răng Hàm Mặt", "location": "Tầng 7 - P.710", "services": "Răng, hàm, mặt", "current_queue": 6, "estimated_wait": 15},
    {"name": "Sản – Phụ khoa", "location": "Tầng 8 - P.801", "services": "Sản khoa, phụ khoa", "current_queue": 8, "estimated_wait": 20},
    {"name": "Nhi khoa", "location": "Tầng 8 - P.805", "services": "Khám nhi", "current_queue": 7, "estimated_wait": 18},
    {"name": "Sức khỏe tâm thần", "location": "Tầng 8 - P.810", "services": "Tâm lý, tâm thần", "current_queue": 2, "estimated_wait": 6},
    {"name": "Phục hồi chức năng", "location": "Tầng 9 - P.901", "services": "Vật lý trị liệu, phục hồi chức năng", "current_queue": 4, "estimated_wait": 12},
    {"name": "Y học cổ truyền", "location": "Tầng 9 - P.905", "services": "Châm cứu, y học cổ truyền", "current_queue": 3, "estimated_wait": 10},
    {"name": "Cấp cứu – Hồi sức tích cực", "location": "Tầng 1 - P.001", "services": "Cấp cứu 24/7", "current_queue": 0, "estimated_wait": 0},
]

PATIENTS = [
    {
        "full_name": "Nguyễn Văn A", "dob": "15/03/1985", "cccd": "001085000001",
        "phone": "0901000001", "is_returning": 1,
        "insurance": {"bhyt_code": "HS0012345678901", "status": "active", "valid_from": "01/01/2026", "valid_to": "31/12/2026", "coverage_percent": 80},
        "appointments": [{"department": "Nội tiết – Đái tháo đường", "appointment_date": "26/07/2026", "appointment_time": "08:30", "status": "scheduled"}],
        "history": [{"department": "Nội tiết – Đái tháo đường", "visit_date": "15/06/2026", "doctor_name": "BS. Phạm Văn X", "notes": "Khám định kỳ tiểu đường"}],
    },
    {
        "full_name": "Trần Thị B", "dob": "22/07/1990", "cccd": "001090000002",
        "phone": "0901000002", "is_returning": 1,
        "insurance": {"bhyt_code": "HS0022345678902", "status": "active", "valid_from": "01/01/2026", "valid_to": "31/12/2026", "coverage_percent": 80},
        "appointments": [{"department": "Tim mạch", "appointment_date": "26/07/2026", "appointment_time": "09:00", "status": "scheduled"}],
        "history": [{"department": "Tim mạch", "visit_date": "10/05/2026", "doctor_name": "BS. Lê Thị Y", "notes": "Tăng huyết áp độ 1"}],
    },
    {
        "full_name": "Lê Văn C", "dob": "10/11/1978", "cccd": "001078000003",
        "phone": "0901000003", "is_returning": 0,
        "insurance": None,
        "appointments": [],
        "history": [],
    },
]


def seed_database():
    """Nạp dữ liệu mẫu (idempotent)."""
    db = SessionLocal()
    try:
        # ── Khoa ──
        for dept in DEPARTMENTS:
            existing = db.query(Department).filter_by(name=dept["name"]).first()
            if existing:
                existing.location = dept.get("location", "")
                existing.services = dept.get("services", "")
            else:
                db.add(Department(**dept))
        db.flush()
        # Xóa khoa cũ không còn trong danh sách (đổi tên / loại bỏ)
        new_names = {d["name"] for d in DEPARTMENTS}
        for old in db.query(Department).all():
            if old.name not in new_names:
                db.delete(old)

        # ── Bệnh nhân + BHYT + lịch hẹn + lịch sử ──
        for p in PATIENTS:
            patient = db.query(Patient).filter_by(cccd=p["cccd"]).first()
            if patient:
                continue
            patient = Patient(
                full_name=p["full_name"],
                dob=p["dob"],
                cccd=p["cccd"],
                phone=p["phone"],
                is_returning=p["is_returning"],
            )
            db.add(patient)
            db.flush()  # lấy patient.id

            ins = p.get("insurance")
            if ins:
                db.add(Insurance(patient_id=patient.id, **ins))

            for appt in p.get("appointments", []):
                db.add(Appointment(patient_id=patient.id, **appt))

            for h in p.get("history", []):
                db.add(VisitHistory(patient_id=patient.id, **h))

        db.commit()
        print("✅ Seed data đã được nạp thành công!")
    finally:
        db.close()


if __name__ == "__main__":
    from app.db.models import init_db
    init_db()
    seed_database()
