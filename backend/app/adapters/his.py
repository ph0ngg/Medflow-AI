"""
Mock HIS Adapter — mô phỏng hệ thống quản lý bệnh viện (HIS/EMR).

Trong prototype, adapter đọc/ghi trực tiếp các bảng Patient/Appointment/
VisitHistory. Khi có HIS thật, thay class này bằng adapter gọi API HIS.
"""
from typing import Optional

from app.adapters.base import IdentityInfo, PatientRecord
from app.db.models import SessionLocal, Patient, Appointment, VisitHistory, Insurance


class MockHISAdapter:
    """Mô phỏng HIS bằng chính database prototype."""

    def _get_by(self, **filters) -> Optional[Patient]:
        db = SessionLocal()
        try:
            return db.query(Patient).filter_by(**filters).first()
        finally:
            db.close()

    def _to_record(self, p: Optional[Patient]) -> PatientRecord:
        if not p:
            return PatientRecord(found=False)
        return PatientRecord(
            patient_id=p.id,
            full_name=p.full_name,
            dob=p.dob or "",
            cccd=p.cccd or "",
            phone=p.phone or "",
            is_returning=bool(p.is_returning),
            found=True,
        )

    def get_patient_by_cccd(self, cccd: str) -> PatientRecord:
        return self._to_record(self._get_by(cccd=cccd))

    def get_patient_by_code(self, code: str) -> PatientRecord:
        return self._to_record(self._get_by(id=code))

    def get_appointments(self, patient_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            rows = (
                db.query(Appointment)
                .filter_by(patient_id=patient_id)
                .order_by(Appointment.appointment_date.desc())
                .all()
            )
            return [
                {
                    "id": a.id,
                    "department": a.department,
                    "appointment_date": a.appointment_date,
                    "appointment_time": a.appointment_time,
                    "status": a.status,
                }
                for a in rows
            ]
        finally:
            db.close()

    def get_visit_history(self, patient_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            rows = (
                db.query(VisitHistory)
                .filter_by(patient_id=patient_id)
                .order_by(VisitHistory.visit_date.desc())
                .all()
            )
            return [
                {
                    "department": v.department,
                    "visit_date": v.visit_date,
                    "doctor_name": v.doctor_name,
                    "notes": v.notes,
                }
                for v in rows
            ]
        finally:
            db.close()

    def register_patient(self, identity: IdentityInfo) -> PatientRecord:
        """Tạo hồ sơ bệnh nhân mới (mô phỏng đăng ký qua HIS).

        Lưu đầy đủ họ tên, ngày sinh, CCCD, quê quán, liên lạc;
        tạo bản ghi BHYT nếu có.
        """
        db = SessionLocal()
        try:
            patient = Patient(
                full_name=identity.full_name or "Bệnh nhân mới",
                dob=identity.dob,
                cccd=identity.cccd or None,
                phone=identity.phone or None,
                address=identity.address or None,
                is_returning=0,
            )
            db.add(patient)
            db.flush()
            if identity.bhyt_code:
                db.add(Insurance(
                    patient_id=patient.id,
                    bhyt_code=identity.bhyt_code,
                    status="active",
                    coverage_percent=80,
                ))
            db.commit()
            db.refresh(patient)
            return PatientRecord(
                patient_id=patient.id,
                full_name=patient.full_name,
                dob=patient.dob or "",
                cccd=patient.cccd or "",
                phone=patient.phone or "",
                address=patient.address or "",
                bhyt_code=identity.bhyt_code or "",
                is_returning=False,
                found=True,
            )
        finally:
            db.close()

    def check_in_appointment(self, appointment_id: int) -> bool:
        db = SessionLocal()
        try:
            appt = db.query(Appointment).filter_by(id=appointment_id).first()
            if not appt:
                return False
            appt.status = "checked_in"
            db.commit()
            return True
        finally:
            db.close()
