"""
Orchestrator - Bộ điều phối luồng chính của MedFlow AI.

─────── LUỒNG XỬ LÝ CHÍNH ───────

1. BỆNH NHÂN TIẾP CẬN KIOSK
   ├── Camera phát hiện khuôn mặt
   ├── Nhận diện → Bệnh nhân cũ / mới
   └── Nếu không nhận diện được → Quét CCCD

2. BỆNH NHÂN CŨ
   ├── Truy xuất thông tin (tên, lịch hẹn, lịch sử khám)
   ├── Chào hỏi + hỏi intent
   │   ├── check_in → Xác nhận lịch hẹn → Cấp số
   │   ├── follow_up → Gợi ý khoa cũ → Cấp số
   │   └── new_visit → Chuyển sang luồng triệu chứng
   └── Kết thúc

3. BỆNH NHÂN MỚI
   ├── Xác thực danh tính (FaceID hoặc CCCD)
   ├── Truy xuất BHYT
   ├── Tiếp nhận triệu chứng bằng giọng nói
   ├── AI phân tích → Hỏi thêm nếu thiếu
   ├── Đề xuất khoa khám
   ├── Kiểm tra hàng đợi
   └── Cấp số thứ tự

4. DẤU HIỆU KHẨN CẤP
   └── Cảnh báo → Hướng dẫn gặp nhân viên y tế
"""
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from services.llm_service import llm_service
from services.triage_service import triage_service
from database import SessionLocal
from database.models import Patient, Appointment, MedicalHistory


class SessionState(str, Enum):
    """Trạng thái của một phiên giao dịch tại kiosk."""
    IDLE = "idle"                           # Chờ bệnh nhân
    DETECTING = "detecting"                 # Đang phát hiện khuôn mặt
    IDENTIFYING = "identifying"             # Đang nhận diện danh tính
    AUTH_CCCD = "auth_cccd"                 # Xác thực qua CCCD
    GREETING = "greeting"                   # Đang chào hỏi
    COLLECTING_SYMPTOMS = "collecting"      # Đang thu thập triệu chứng
    TRIAGING = "triaging"                   # Đang phân luồng
    ISSUING_TICKET = "issuing"              # Đang cấp số
    EMERGENCY = "emergency"                 # Cảnh báo khẩn cấp
    DONE = "done"                           # Hoàn tất


@dataclass
class KioskSession:
    """Lưu trạng thái một phiên của bệnh nhân tại kiosk."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: SessionState = SessionState.IDLE
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    is_returning: bool = False
    symptoms: list[str] = field(default_factory=list)
    suggested_department: Optional[str] = None
    ticket_number: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "patient_name": self.patient_name,
            "is_returning": self.is_returning,
            "symptoms": self.symptoms,
            "suggested_department": self.suggested_department,
            "ticket_number": self.ticket_number,
        }


class KioskOrchestrator:
    """
    Điều phối toàn bộ luồng tương tác giữa bệnh nhân và kiosk.
    Đây là "bộ não" của MedFlow AI.
    """

    def __init__(self):
        self.sessions: dict[str, KioskSession] = {}

    # ── Bước 1: Phát hiện & Nhận diện ──────────────────

    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Xử lý một frame từ camera.
        Phát hiện khuôn mặt → Nhận diện → Trả về thông tin.

        Returns:
            dict chứa thông tin về người được phát hiện.
        """
        from services.face_service import face_service

        faces = face_service.detect_faces(frame)
        if not faces:
            return {"detected": False, "faces": []}

        result_faces = []
        for face in faces:
            face_id, face_name = face_service.identify_face(face)
            result_faces.append({
                "id": face_id,
                "name": face_name if face_name else None,
                "bbox": face.bounding_box.tolist() if hasattr(face.bounding_box, 'tolist') else face.bounding_box,
            })

        return {
            "detected": True,
            "faces": result_faces,
        }

    # ── Bước 2: Khởi tạo phiên ──────────────────────────

    def start_session(self, face_name: str = None, face_id: str = None) -> KioskSession:
        """
        Bắt đầu phiên mới cho bệnh nhân.
        Nếu nhận diện được → bệnh nhân cũ.
        Nếu không → bệnh nhân mới.
        """
        session = KioskSession()

        if face_name and face_id:
            session.is_returning = True
            session.patient_name = face_name
            session.state = SessionState.GREETING
            # Tìm patient_id từ database
            db = SessionLocal()
            try:
                # Tìm theo tên (tạm thời, sau này map qua FAISS id)
                patient = db.query(Patient).filter_by(full_name=face_name).first()
                if patient:
                    session.patient_id = patient.id
            finally:
                db.close()
        else:
            session.is_returning = False
            session.state = SessionState.IDENTIFYING

        self.sessions[session.session_id] = session
        return session

    # ── Bước 3: Lấy context bệnh nhân ───────────────────

    def get_patient_context(self, session: KioskSession) -> dict:
        """Truy xuất thông tin bệnh nhân từ DB."""
        if not session.patient_id:
            return {}

        db = SessionLocal()
        try:
            patient = db.query(Patient).filter_by(id=session.patient_id).first()
            if not patient:
                return {}

            # Lịch hẹn sắp tới
            appointments = (
                db.query(Appointment)
                .filter_by(patient_id=patient.id, status="scheduled")
                .all()
            )

            # Lịch sử khám (khoa gần nhất)
            last_visit = (
                db.query(MedicalHistory)
                .filter_by(patient_id=patient.id)
                .order_by(MedicalHistory.visit_date.desc())
                .first()
            )

            return {
                "full_name": patient.full_name,
                "dob": patient.dob,
                "bhyt_code": patient.bhyt_code,
                "upcoming_appointments": [
                    {"department": a.department, "date": a.appointment_date}
                    for a in appointments
                ],
                "last_department": last_visit.department if last_visit else None,
            }
        finally:
            db.close()

    # ── Bước 4: Xử lý hội thoại ─────────────────────────

    def process_message(self, session_id: str, user_message: str) -> dict:
        """
        Xử lý tin nhắn thoại/text từ bệnh nhân.
        Đây là bước cốt lõi của luồng hội thoại.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session không tồn tại"}

        # Lấy context
        patient_context = self.get_patient_context(session)

        # Gửi đến LLM
        llm_result = llm_service.chat(session_id, user_message, patient_context)

        # Cập nhật session
        session.symptoms = llm_result.get("symptoms", [])

        intent = llm_result.get("intent", "new_visit")

        # ── Xử lý theo intent ──
        if intent == "emergency":
            session.state = SessionState.EMERGENCY
            return {
                **llm_result,
                "state": session.state.value,
                "action": "alert_staff",
            }

        elif intent == "check_in":
            session.state = SessionState.ISSUING_TICKET
            # Tìm lịch hẹn và cấp số
            dept = patient_context.get("upcoming_appointments", [{}])[0].get("department")
            if dept:
                ticket = triage_service.issue_ticket(session.patient_id, dept)
                session.ticket_number = ticket["ticket_number"] if ticket else None
                return {
                    **llm_result,
                    "state": session.state.value,
                    "department": dept,
                    "ticket": ticket,
                }
            return {**llm_result, "state": session.state.value}

        elif intent == "follow_up":
            last_dept = patient_context.get("last_department")
            if last_dept:
                queue_info = triage_service.get_queue_info(last_dept)
                session.suggested_department = last_dept
                session.state = SessionState.TRIAGING
                return {
                    **llm_result,
                    "state": session.state.value,
                    "suggested_department": last_dept,
                    "   queue_info": queue_info,
                }
            session.state = SessionState.COLLECTING_SYMPTOMS
            return {**llm_result, "state": session.state.value}

        elif intent == "new_visit":
            if llm_result.get("need_more_info"):
                session.state = SessionState.COLLECTING_SYMPTOMS
                return {**llm_result, "state": session.state.value}
            else:
                # Đủ thông tin → phân luồng
                return self._triage_and_issue(session, llm_result)

        return {**llm_result, "state": session.state.value}

    # ── Bước 5: Phân luồng & Cấp số ─────────────────────

    def _triage_and_issue(self, session: KioskSession, llm_result: dict) -> dict:
        """Phân luồng và cấp số cho bệnh nhân."""
        symptoms = session.symptoms
        user_text = llm_result.get("response", "")

        # Kiểm tra khẩn cấp
        if triage_service.check_emergency(symptoms, user_text):
            session.state = SessionState.EMERGENCY
            return {
                "intent": "emergency",
                "state": session.state.value,
                "response": "Các triệu chứng anh/chị cung cấp có thể cần được nhân viên y tế đánh giá ngay. Vui lòng liên hệ nhân viên y tế gần nhất.",
                "action": "alert_staff",
            }

        # Đề xuất khoa
        dept = triage_service.suggest_department(symptoms)
        if dept:
            session.suggested_department = dept
            session.state = SessionState.TRIAGING

            queue_info = triage_service.get_queue_info(dept)
            return {
                "intent": "new_visit",
                "state": session.state.value,
                "suggested_department": dept,
                "queue_info": queue_info,
                "response": f"Dựa trên thông tin anh/chị cung cấp, hệ thống đề xuất đăng ký khám tại {dept}. Hiện có {queue_info['current_queue']} người đang chờ, thời gian chờ dự kiến {queue_info['estimated_wait']} phút.",
            }

        session.state = SessionState.COLLECTING_SYMPTOMS
        return {
            "intent": "new_visit",
            "state": session.state.value,
            "response": "Anh/chị vui lòng mô tả thêm triệu chứng để tôi có thể hỗ trợ chính xác hơn.",
        }

    # ── Bước 6: Xác nhận & cấp số ───────────────────────

    def confirm_and_issue(self, session_id: str) -> dict:
        """Bệnh nhân xác nhận → cấp số thứ tự."""
        session = self.sessions.get(session_id)
        if not session or not session.suggested_department:
            return {"error": "Chưa có khoa được đề xuất"}

        ticket = triage_service.issue_ticket(session.patient_id or 0, session.suggested_department)
        session.ticket_number = ticket["ticket_number"] if ticket else None
        session.state = SessionState.DONE

        return {
            "state": session.state.value,
            "ticket": ticket,
            "response": f"Đã cấp số thứ tự {ticket['ticket_number']} tại {session.suggested_department}. Xin vui lòng chờ đến lượt.",
        }

    # ── Quản lý session ──────────────────────────────────

    def get_session(self, session_id: str) -> KioskSession | None:
        return self.sessions.get(session_id)

    def end_session(self, session_id: str):
        """Kết thúc phiên."""
        self.sessions.pop(session_id, None)
        llm_service.reset_session(session_id)


# Singleton
orchestrator = KioskOrchestrator()
