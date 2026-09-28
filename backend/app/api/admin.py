"""
API Routes — Admin (dashboard quản trị cơ bản).

PRD mục 12.2 (should-have): Dashboard quản trị cơ bản.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db.models import (
    SessionLocal, Patient, Department, QueueTicket, Payment, Conversation,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PatientCreate(BaseModel):
    full_name: str
    dob: str = ""
    cccd: str = ""
    phone: str = ""


# ── Thống kê tổng quan ─────────────────────────────────
@router.get("/stats")
async def stats():
    db = SessionLocal()
    try:
        return JSONResponse({
            "patients": db.query(Patient).count(),
            "departments": db.query(Department).count(),
            "waiting_tickets": db.query(QueueTicket).filter_by(status="waiting").count(),
            "payments": db.query(Payment).count(),
            "paid_amount": db.query(Payment).filter_by(status="paid").count(),
            "conversations": db.query(Conversation).count(),
        })
    finally:
        db.close()


# ── Bệnh nhân ──────────────────────────────────────────
@router.get("/patients")
async def list_patients():
    db = SessionLocal()
    try:
        rows = db.query(Patient).all()
        return JSONResponse([
            {
                "id": p.id, "full_name": p.full_name, "dob": p.dob,
                "cccd": p.cccd, "phone": p.phone,
                "is_returning": bool(p.is_returning),
            }
            for p in rows
        ])
    finally:
        db.close()


@router.post("/patients")
async def create_patient(data: PatientCreate):
    db = SessionLocal()
    try:
        if db.query(Patient).filter_by(cccd=data.cccd).first():
            raise HTTPException(status_code=400, detail="CCCD đã tồn tại")
        patient = Patient(**data.model_dump())
        db.add(patient)
        db.commit()
        return JSONResponse({"message": f"Đã thêm bệnh nhân {data.full_name}"})
    finally:
        db.close()


# ── Khoa / Hàng đợi ────────────────────────────────────
@router.get("/departments")
async def list_departments():
    db = SessionLocal()
    try:
        rows = db.query(Department).all()
        return JSONResponse([
            {
                "id": d.id, "name": d.name, "location": d.location,
                "services": d.services, "current_queue": d.current_queue,
                "estimated_wait": d.estimated_wait, "is_active": bool(d.is_active),
            }
            for d in rows
        ])
    finally:
        db.close()


@router.put("/departments/{dept_id}")
async def update_department(dept_id: int, data: dict):
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(id=dept_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy khoa")
        for field in ("current_queue", "estimated_wait", "is_active", "location", "services"):
            if field in data:
                setattr(dept, field, data[field])
        db.commit()
        return JSONResponse({"message": "Đã cập nhật"})
    finally:
        db.close()


@router.get("/queue")
async def list_queue():
    db = SessionLocal()
    try:
        rows = (
            db.query(QueueTicket)
            .order_by(QueueTicket.created_at.desc())
            .limit(100)
            .all()
        )
        return JSONResponse([
            {
                "id": t.id, "patient_id": t.patient_id,
                "department_id": t.department_id,
                "department": t.department.name if t.department else "",
                "ticket_number": t.ticket_number, "status": t.status,
                "created_at": str(t.created_at),
            }
            for t in rows
        ])
    finally:
        db.close()


# ── Thanh toán / Hội thoại ─────────────────────────────
@router.get("/payments")
async def list_payments():
    db = SessionLocal()
    try:
        rows = db.query(Payment).order_by(Payment.created_at.desc()).limit(100).all()
        return JSONResponse([
            {
                "id": p.id, "patient_id": p.patient_id, "amount": p.amount,
                "insurance_covered": p.insurance_covered, "patient_pay": p.patient_pay,
                "method": p.method, "status": p.status,
            }
            for p in rows
        ])
    finally:
        db.close()


@router.get("/conversations")
async def list_conversations():
    db = SessionLocal()
    try:
        rows = db.query(Conversation).order_by(Conversation.created_at.desc()).limit(100).all()
        return JSONResponse([
            {
                "id": c.id, "session_id": c.session_id, "intent": c.intent,
                "transcript": c.transcript, "summary": c.summary,
                "created_at": str(c.created_at),
            }
            for c in rows
        ])
    finally:
        db.close()
