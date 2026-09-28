"""
Service Phân luồng (Triage).
Dựa trên triệu chứng → đề xuất khoa khám phù hợp.
Kiểm tra dấu hiệu khẩn cấp.
"""
from config import EMERGENCY_KEYWORDS, DEPARTMENT_MAPPING


class TriageService:
    """
    Phân tích triệu chứng, đề xuất khoa khám.
    KHÔNG chẩn đoán bệnh - chỉ hỗ trợ phân luồng.
    """

    def check_emergency(self, symptoms: list[str], user_text: str = "") -> bool:
        """
        Kiểm tra xem có dấu hiệu khẩn cấp không.
        """
        combined = " ".join(symptoms) + " " + user_text
        combined_lower = combined.lower()
        return any(kw in combined_lower for kw in EMERGENCY_KEYWORDS)

    def suggest_department(self, symptoms: list[str]) -> str | None:
        """
        Đề xuất khoa khám dựa trên triệu chứng.
        Dùng keyword matching đơn giản (sẽ nâng cấp lên LLM/rule engine sau).
        """
        combined = " ".join(symptoms).lower()

        scores = {}
        for dept, keywords in DEPARTMENT_MAPPING.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[dept] = score

        if not scores:
            return None

        # Trả về khoa có điểm cao nhất
        return max(scores, key=scores.get)

    def get_queue_info(self, department_name: str) -> dict:
        """
        Lấy thông tin hàng đợi của một khoa.
        """
        from database import SessionLocal, Department
        db = SessionLocal()
        try:
            dept = db.query(Department).filter_by(name=department_name).first()
            if dept:
                return {
                    "department": dept.name,
                    "current_queue": dept.current_queue,
                    "estimated_wait": dept.estimated_wait,
                }
            return {"department": department_name, "current_queue": 0, "estimated_wait": 0}
        finally:
            db.close()

    def issue_ticket(self, patient_id: int, department_name: str) -> dict | None:
        """
        Cấp số thứ tự cho bệnh nhân tại khoa.
        """
        from database import SessionLocal, Department, QueueTicket
        db = SessionLocal()
        try:
            dept = db.query(Department).filter_by(name=department_name).first()
            if not dept:
                return None

            dept.current_queue += 1
            ticket_number = dept.current_queue

            ticket = QueueTicket(
                patient_id=patient_id,
                department_id=dept.id,
                ticket_number=ticket_number,
            )
            db.add(ticket)
            db.commit()

            return {
                "ticket_number": ticket_number,
                "department": department_name,
                "estimated_wait": dept.estimated_wait,
            }
        finally:
            db.close()


# Singleton
triage_service = TriageService()
