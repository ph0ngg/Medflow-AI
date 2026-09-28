"""
Mock Queue Adapter — mô phỏng hệ thống hàng đợi / lấy số.
"""
from app.adapters.base import QueueInfo
from app.db.models import SessionLocal, Department, QueueTicket


class MockQueueAdapter:
    def list_departments(self) -> list[dict]:
        db = SessionLocal()
        try:
            rows = db.query(Department).filter_by(is_active=1).all()
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "location": d.location,
                    "services": d.services,
                    "current_queue": d.current_queue,
                    "estimated_wait": d.estimated_wait,
                }
                for d in rows
            ]
        finally:
            db.close()

    def get_queue_info(self, department: str) -> QueueInfo:
        db = SessionLocal()
        try:
            dept = db.query(Department).filter_by(name=department).first()
            if not dept:
                return QueueInfo(department=department)
            return QueueInfo(
                department=dept.name,
                current_queue=dept.current_queue,
                estimated_wait=dept.estimated_wait,
                now_serving=max(0, dept.current_queue - 1),
            )
        finally:
            db.close()

    def issue_ticket(self, patient_id: int, department: str) -> dict:
        db = SessionLocal()
        try:
            dept = db.query(Department).filter_by(name=department).first()
            if not dept:
                return {"error": "department_not_found"}

            dept.current_queue += 1
            ticket_number = dept.current_queue
            ticket = QueueTicket(
                patient_id=patient_id,
                department_id=dept.id,
                ticket_number=ticket_number,
                status="waiting",
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return {
                "ticket_id": ticket.id,
                "ticket_number": ticket_number,
                "department": dept.name,
                "location": dept.location,
                "estimated_wait": dept.estimated_wait,
            }
        finally:
            db.close()
