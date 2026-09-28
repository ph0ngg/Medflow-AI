"""
Mock Insurance Adapter — mô phỏng hệ thống BHYT.
"""
from app.adapters.base import InsuranceRecord
from app.db.models import SessionLocal, Insurance


class MockInsuranceAdapter:
    def verify(self, bhyt_code: str) -> InsuranceRecord:
        if not bhyt_code:
            return InsuranceRecord(bhyt_code="", status="invalid", valid=False)

        db = SessionLocal()
        try:
            row = db.query(Insurance).filter_by(bhyt_code=bhyt_code).first()
            if not row:
                return InsuranceRecord(bhyt_code=bhyt_code, status="invalid", valid=False)
            return InsuranceRecord(
                bhyt_code=row.bhyt_code,
                status=row.status,
                coverage_percent=row.coverage_percent,
                valid=(row.status == "active"),
            )
        finally:
            db.close()
