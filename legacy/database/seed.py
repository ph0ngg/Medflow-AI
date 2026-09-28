"""
Dữ liệu mẫu (seed data) cho demo MedFlow AI.
"""
from database.models import SessionLocal, Patient, Appointment, MedicalHistory, Department


def seed_database():
    """Nạp dữ liệu mẫu vào database."""
    db = SessionLocal()

    # ── Khoa ──────────────────────────────────────────
    departments = [
        {"name": "Nội tiêu hóa", "current_queue": 8, "estimated_wait": 20},
        {"name": "Nội tim mạch", "current_queue": 5, "estimated_wait": 15},
        {"name": "Nội hô hấp", "current_queue": 3, "estimated_wait": 10},
        {"name": "Nội tiết", "current_queue": 12, "estimated_wait": 30},
        {"name": "Cơ xương khớp", "current_queue": 7, "estimated_wait": 18},
        {"name": "Da liễu", "current_queue": 2, "estimated_wait": 5},
        {"name": "Tai Mũi Họng", "current_queue": 10, "estimated_wait": 25},
        {"name": "Mắt", "current_queue": 4, "estimated_wait": 12},
    ]
    for dept in departments:
        if not db.query(Department).filter_by(name=dept["name"]).first():
            db.add(Department(**dept))

    # ── Bệnh nhân mẫu ─────────────────────────────────
    patients = [
        {
            "full_name": "Nguyễn Văn A",
            "dob": "15/03/1985",
            "cccd": "001085000001",
            "bhyt_code": "HS0012345678901",
            "is_returning": 1,
        },
        {
            "full_name": "Trần Thị B",
            "dob": "22/07/1990",
            "cccd": "001090000002",
            "bhyt_code": "HS0022345678902",
            "is_returning": 1,
        },
        {
            "full_name": "Lê Văn C",
            "dob": "10/11/1978",
            "cccd": "001078000003",
            "bhyt_code": "HS0032345678903",
            "is_returning": 0,
        },
    ]
    for p in patients:
        if not db.query(Patient).filter_by(cccd=p["cccd"]).first():
            db.add(Patient(**p))

    db.commit()

    # ── Lịch hẹn mẫu ──────────────────────────────────
    pa = db.query(Patient).filter_by(cccd="001085000001").first()
    if pa and not db.query(Appointment).filter_by(patient_id=pa.id).first():
        db.add(Appointment(
            patient_id=pa.id,
            department="Nội tiết",
            appointment_date="26/07/2026",
            status="scheduled",
        ))

    # ── Lịch sử khám mẫu ──────────────────────────────
    if pa and not db.query(MedicalHistory).filter_by(patient_id=pa.id).first():
        db.add(MedicalHistory(
            patient_id=pa.id,
            department="Nội tiết",
            visit_date="15/06/2026",
            doctor_name="BS. Phạm Văn X",
            notes="Khám định kỳ tiểu đường",
        ))

    db.commit()
    db.close()
    print("✅ Seed data đã được nạp thành công!")


if __name__ == "__main__":
    from database.models import init_db
    init_db()
    seed_database()
