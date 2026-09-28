"""
API Routes cho Admin - Quản lý dữ liệu.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import SessionLocal
from database.models import Patient, Department, QueueTicket

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PatientCreate(BaseModel):
    full_name: str
    dob: str = ""
    cccd: str = ""
    bhyt_code: str = ""


@router.get("/patients")
async def list_patients():
    """Danh sách bệnh nhân."""
    db = SessionLocal()
    try:
        patients = db.query(Patient).all()
        return JSONResponse([
            {
                "id": p.id,
                "full_name": p.full_name,
                "dob": p.dob,
                "cccd": p.cccd,
                "bhyt_code": p.bhyt_code,
                "is_returning": bool(p.is_returning),
            }
            for p in patients
        ])
    finally:
        db.close()


@router.post("/patients")
async def create_patient(data: PatientCreate):
    """Thêm bệnh nhân mới."""
    db = SessionLocal()
    try:
        patient = Patient(**data.model_dump())
        db.add(patient)
        db.commit()
        return JSONResponse({"message": f"Đã thêm bệnh nhân {data.full_name}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/departments")
async def list_departments():
    """Danh sách khoa + hàng đợi."""
    db = SessionLocal()
    try:
        depts = db.query(Department).all()
        return JSONResponse([
            {
                "id": d.id,
                "name": d.name,
                "current_queue": d.current_queue,
                "estimated_wait": d.estimated_wait,
            }
            for d in depts
        ])
    finally:
        db.close()


@router.get("/queue")
async def list_queue():
    """Danh sách hàng đợi hiện tại."""
    db = SessionLocal()
    try:
        tickets = (
            db.query(QueueTicket)
            .filter_by(status="waiting")
            .order_by(QueueTicket.created_at.desc())
            .limit(50)
            .all()
        )
        return JSONResponse([
            {
                "id": t.id,
                "patient_id": t.patient_id,
                "department_id": t.department_id,
                "ticket_number": t.ticket_number,
                "status": t.status,
            }
            for t in tickets
        ])
    finally:
        db.close()
