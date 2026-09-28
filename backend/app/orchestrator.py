"""
Orchestrator — bộ điều phối luồng chính MedFlow AI (state machine).

Triển khai luồng theo PRD mục 6:
- Bệnh nhân cũ: phát hiện → xác thực → hồ sơ → nhu cầu → đề xuất → queue → xác nhận → ticket.
- Bệnh nhân mới: xác thực CCCD → hồ sơ → triệu chứng → đề xuất → queue → thanh toán → xác nhận → ticket.
- Red flag: dừng luồng cấp số thông thường, hướng dẫn gặp nhân viên y tế.
"""
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from app.config import SESSION_TIMEOUT_SECONDS
from app.session import KioskSession, SessionState
from app.services.llm_service import llm_service
from app.services.triage_service import triage_service
from app.adapters import (
    get_his_adapter, get_insurance_adapter, get_queue_adapter,
    get_payment_adapter, get_identity_adapter,
)
from app.adapters.base import IdentityInfo
from app.rules import (
    is_confirmation_yes, is_confirmation_no,
)
from app.db.models import SessionLocal, Patient, Insurance, Conversation

EMERGENCY_RESPONSE = (
    "Các triệu chứng anh/chị cung cấp có thể cần được nhân viên y tế đánh giá ngay. "
    "Vui lòng liên hệ nhân viên y tế gần nhất."
)


class KioskOrchestrator:
    def __init__(self):
        self.sessions: dict[str, KioskSession] = {}

    # ── 1. Phát hiện & nhận diện ────────────────────────
    def process_frame(self, frame: np.ndarray) -> dict:
        from app.services.face_service import face_service

        faces = face_service.detect_faces(frame)
        if not faces:
            return {"detected": False, "faces": [], "available": face_service.available}

        result_faces = []
        for face in faces:
            face_id, face_name = face_service.identify_face(face)
            bbox = getattr(face, "bounding_box", None)
            result_faces.append({
                "id": str(face_id) if face_id else None,
                "name": face_name or None,
                "bbox": bbox.tolist() if hasattr(bbox, "tolist") else bbox,
            })

        return {
            "detected": True,
            "faces": result_faces,
            "available": face_service.available,
        }

    # ── 2. Khởi tạo phiên ───────────────────────────────
    def start_session(
        self, face_name: str | None = None, face_id: str | None = None
    ) -> KioskSession:
        session = KioskSession()

        if face_name and face_id:
            session.is_returning = True
            session.patient_name = face_name
            session.identity_method = "face"
            session.state = SessionState.GREETING
            self._link_patient_by_face(session, face_id, face_name)
        else:
            session.is_returning = False
            session.state = SessionState.IDENTIFYING

        self.sessions[session.session_id] = session
        return session

    def _link_patient_by_face(self, session: KioskSession, face_id: str, face_name: str):
        """Gắn bệnh nhân từ kết quả nhận diện mặt.

        Thứ tự ưu tiên: face_id → full_name → tạo hồ sơ mới (demo).
        Đảm bảo sau nhận diện thành công KHÔNG quay lại bước nhập CCCD.
        """
        db = SessionLocal()
        try:
            patient = None
            if face_id:
                patient = db.query(Patient).filter_by(face_id=str(face_id)).first()
            if not patient and face_name:
                patient = db.query(Patient).filter_by(full_name=face_name).first()
            if not patient and face_name:
                patient = Patient(
                    full_name=face_name,
                    face_id=str(face_id) if face_id else None,
                    is_returning=1,
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)

            if patient:
                session.patient_id = patient.id
                session.patient_name = patient.full_name
                session.is_returning = True
                self._attach_insurance(session, patient)
        finally:
            db.close()

    def _attach_insurance(self, session: KioskSession, patient: Patient):
        """Gắn thông tin BHYT của bệnh nhân vào session."""
        session.bhyt_code = None
        session.insurance_valid = False
        if not patient:
            return
        db = SessionLocal()
        try:
            ins = db.query(Insurance).filter_by(patient_id=patient.id).first()
            if ins:
                session.bhyt_code = ins.bhyt_code
                record = get_insurance_adapter().verify(ins.bhyt_code)
                session.insurance_valid = record.valid
                session.insurance_status = record.status
        finally:
            db.close()

    # ── 3. Xác thực qua CCCD ────────────────────────────
    def verify_cccd(self, session_id: str, cccd: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session không tồn tại"}

        identity = get_identity_adapter().verify_cccd(cccd)
        if not identity.valid:
            session.state = SessionState.AUTH_CCCD
            return {
                **session.to_dict(),
                "error": "invalid_cccd",
                "response": "Mã CCCD không hợp lệ. Anh/chị vui lòng thử lại hoặc gọi nhân viên hỗ trợ.",
            }

        his = get_his_adapter()
        patient = his.get_patient_by_cccd(cccd)
        if patient.found:
            session.patient_id = patient.patient_id
            session.patient_name = patient.full_name
            session.is_returning = patient.is_returning
        else:
            # Bệnh nhân mới → tạo hồ sơ (mô phỏng)
            created = his.register_patient(identity)
            session.patient_id = created.patient_id
            session.patient_name = created.full_name
            session.is_returning = False

        session.cccd = cccd
        session.identity_method = "cccd"
        session.state = SessionState.PROFILE_REVIEW

        db = SessionLocal()
        try:
            patient_obj = db.query(Patient).filter_by(id=session.patient_id).first()
            if patient_obj:
                self._attach_insurance(session, patient_obj)
        finally:
            db.close()

        return {**session.to_dict(), **self.get_profile(session)}

    def register_patient(
        self,
        full_name: str,
        dob: str,
        address: str = "",
        phone: str = "",
        cccd: str | None = None,
        bhyt_code: str | None = None,
        face_image=None,
    ) -> dict:
        """Đăng ký bệnh nhân mới từ form kiosk.

        Yêu cầu bắt buộc: họ tên, ngày sinh, và (CCCD hoặc BHYT).
        `face_image` (numpy array, tùy chọn): đăng ký khuôn mặt để đăng nhập bằng mặt.
        """
        full_name = (full_name or "").strip()
        dob = (dob or "").strip()
        address = (address or "").strip()
        phone = (phone or "").strip()
        cccd = (cccd or "").strip() or None
        bhyt_code = (bhyt_code or "").strip() or None

        if not full_name:
            return {"error": "missing_fullname", "response": "Vui lòng nhập họ tên."}
        if not dob:
            return {"error": "missing_dob", "response": "Vui lòng nhập ngày sinh."}
        if not cccd and not bhyt_code:
            return {"error": "missing_id", "response": "Vui lòng nhập số CCCD hoặc số BHYT."}

        his = get_his_adapter()
        if cccd and his.get_patient_by_cccd(cccd).found:
            return {
                "error": "cccd_exists",
                "response": "CCCD này đã được đăng ký. Vui lòng đăng nhập bằng CCCD.",
            }

        identity = IdentityInfo(
            full_name=full_name, dob=dob, cccd=cccd or "",
            address=address, phone=phone, bhyt_code=bhyt_code or "", valid=True,
        )
        record = his.register_patient(identity)

        # Đăng ký khuôn mặt (tùy chọn) → lưu embedding + link face_id
        faiss_id: int | None = None
        face_registered = False
        if face_image is not None:
            from app.services.face_service import face_service
            faiss_id = face_service.register_face(face_image, full_name)
            face_registered = faiss_id is not None

        session = KioskSession()
        session.patient_id = record.patient_id
        session.patient_name = record.full_name
        session.cccd = cccd
        session.bhyt_code = bhyt_code
        session.identity_method = "register"
        session.is_returning = False
        session.state = SessionState.GREETING
        self.sessions[session.session_id] = session

        db = SessionLocal()
        try:
            patient = db.query(Patient).filter_by(id=record.patient_id).first()
            if patient:
                if face_registered and faiss_id is not None:
                    patient.face_id = str(faiss_id)
                    db.commit()
                self._attach_insurance(session, patient)
        finally:
            db.close()

        note = (
            " Khuôn mặt đã được lưu — lần sau có thể đăng nhập bằng khuôn mặt."
            if face_registered else ""
        )
        return {
            **session.to_dict(),
            **self.get_profile(session),
            "face_registered": face_registered,
            "message": f"Đăng ký thành công! Xin chào {record.full_name}." + note,
        }

    # ── 4. Hồ sơ bệnh nhân ──────────────────────────────
    def get_profile(self, session: KioskSession) -> dict:
        if not session.patient_id:
            return {}
        his = get_his_adapter()
        appointments = his.get_appointments(session.patient_id)
        history = his.get_visit_history(session.patient_id)
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter_by(id=session.patient_id).first()
            profile = {
                "full_name": patient.full_name if patient else session.patient_name,
                "dob": patient.dob if patient else "",
                "cccd": patient.cccd if patient else session.cccd,
                "phone": patient.phone if patient else "",
                "address": patient.address if patient else "",
                "bhyt_code": session.bhyt_code,
                "insurance_valid": session.insurance_valid,
                "insurance_status": session.insurance_status,
                "upcoming_appointments": [
                    a for a in appointments if a.get("status") == "scheduled"
                ],
                "last_department": history[0]["department"] if history else None,
                "history": history,
            }
            return {"profile": profile}
        finally:
            db.close()

    # ── 5. Xử lý hội thoại ──────────────────────────────
    def process_message(self, session_id: str, user_message: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session không tồn tại"}
        session.add_message("user", user_message)

        # 1) Red flag (rule, luôn ưu tiên cao nhất)
        combined = user_message + " " + " ".join(session.symptoms)
        if triage_service.check_emergency(combined):
            session.state = SessionState.EMERGENCY
            self._save_conversation(session, "emergency")
            return {
                "intent": "emergency",
                "state": session.state.value,
                "response": EMERGENCY_RESPONSE,
                "action": "alert_staff",
            }

        # 2) Xử lý xác nhận theo state hiện tại (deterministic)
        if session.state == SessionState.TRIAGING:
            if is_confirmation_yes(user_message):
                return self._start_registration(session)
            if is_confirmation_no(user_message):
                session.state = SessionState.COLLECTING
                return {
                    "intent": "new_visit",
                    "state": session.state.value,
                    "response": "Anh/chị muốn khám khoa nào? Tôi có thể gợi ý dựa trên triệu chứng, hoặc anh/chị chọn khoa trên màn hình.",
                    "departments": triage_service.list_departments(),
                }

        if session.state == SessionState.PAYMENT:
            if is_confirmation_yes(user_message):
                return self.process_payment(session_id)
            if is_confirmation_no(user_message):
                session.payment = None
                session.state = SessionState.TRIAGING
                return {
                    "intent": "payment",
                    "state": session.state.value,
                    "response": "Anh/chị có thể đăng ký khám mà không thanh toán qua kiosk. Anh/chị xác nhận đăng ký tại khoa {0} chứ?".format(session.suggested_department),
                }

        if session.state == SessionState.CONFIRMING:
            if is_confirmation_yes(user_message):
                return self.confirm_and_issue(session_id)
            if is_confirmation_no(user_message):
                session.state = SessionState.TRIAGING
                return {
                    "intent": "confirm",
                    "state": session.state.value,
                    "response": "Anh/chị muốn thay đổi khoa khám hoặc hủy đăng ký?",
                }

        # 3) LLM intent
        context = self.get_profile(session).get("profile", {}) or {}
        llm_result = llm_service.chat(session_id, user_message, context)
        intent = llm_result.get("intent", "new_visit")
        session.intent = intent
        session.symptoms = self._merge(session.symptoms, llm_result.get("symptoms", []))
        session.add_message("assistant", llm_result.get("response", ""))

        # 4) Yêu cầu xác thực nếu chưa có định danh
        if session.patient_id is None and intent in ("new_visit", "check_in", "follow_up"):
            session.state = SessionState.IDENTIFYING
            return {
                "intent": intent,
                "state": session.state.value,
                "response": "Để tiếp tục, anh/chị vui lòng quét CCCD hoặc nhập mã bệnh nhân để xác thực danh tính.",
            }

        # 5) Dispatch theo intent
        if intent == "emergency":
            session.state = SessionState.EMERGENCY
            self._save_conversation(session, "emergency")
            return {"intent": intent, "state": session.state.value, "response": EMERGENCY_RESPONSE, "action": "alert_staff"}

        if intent == "check_in":
            return self._handle_check_in(session, llm_result)
        if intent == "follow_up":
            return self._handle_follow_up(session, llm_result)
        if intent in ("payment", "lookup", "support"):
            return self._handle_other(session, llm_result)

        return self._handle_new_visit(session, llm_result)

    # ── Handlers theo intent ────────────────────────────
    def _handle_check_in(self, session: KioskSession, llm: dict) -> dict:
        his = get_his_adapter()
        appointments = [a for a in his.get_appointments(session.patient_id or 0)
                        if a.get("status") == "scheduled"]
        if not appointments:
            session.state = SessionState.COLLECTING
            return {
                "intent": "check_in",
                "state": session.state.value,
                "response": "Không tìm thấy lịch hẹn sắp tới của anh/chị. Nếu anh/chị có triệu chứng mới, vui lòng mô tả để tôi hỗ trợ đăng ký khám.",
            }

        appt = appointments[0]
        his.check_in_appointment(appt["id"])
        session.suggested_department = appt["department"]
        session.dept_reason = "Theo lịch hẹn đã đăng ký"
        session.dept_confidence = 1.0
        session.state = SessionState.TRIAGING
        session.queue_info = triage_service.get_queue_info(appt["department"])
        qi = session.queue_info
        return {
            "intent": "check_in",
            "state": session.state.value,
            "suggested_department": appt["department"],
            "queue_info": qi,
            "response": (
                f"Anh/chị có lịch hẹn tại khoa {appt['department']} vào {appt['appointment_date']} "
                f"{appt.get('appointment_time', '')}. Hiện có {qi['current_queue']} người đang chờ, "
                f"thời gian chờ dự kiến {qi['estimated_wait']} phút. Anh/chị xác nhận check-in chứ?"
            ),
        }

    def _handle_follow_up(self, session: KioskSession, llm: dict) -> dict:
        his = get_his_adapter()
        history = his.get_visit_history(session.patient_id or 0)
        if history:
            dept = history[0]["department"]
            session.suggested_department = dept
            session.dept_reason = "Theo lịch sử khám gần nhất"
            session.dept_confidence = 0.9
            session.state = SessionState.TRIAGING
            session.queue_info = triage_service.get_queue_info(dept)
            qi = session.queue_info
            return {
                "intent": "follow_up",
                "state": session.state.value,
                "suggested_department": dept,
                "queue_info": qi,
                "response": (
                    f"Lần khám gần nhất của anh/chị tại khoa {dept}. "
                    f"Hiện có {qi['current_queue']} người đang chờ, thời gian chờ {qi['estimated_wait']} phút. "
                    f"Anh/chị muốn tái khám tại khoa này chứ?"
                ),
            }
        session.state = SessionState.COLLECTING
        return {
            "intent": "follow_up",
            "state": session.state.value,
            "response": "Tôi chưa tìm thấy lịch sử khám. Anh/chị vui lòng mô tả triệu chứng hiện tại để tôi hỗ trợ.",
        }

    def _propose_department(self, session: KioskSession, suggestion, intent: str = "new_visit") -> dict:
        """Chuyển sang TRIAGING với khoa đề xuất + queue info."""
        session.suggested_department = suggestion.department
        session.dept_reason = suggestion.reason
        session.dept_confidence = suggestion.confidence
        session.state = SessionState.TRIAGING
        session.queue_info = triage_service.get_queue_info(suggestion.department)
        qi = session.queue_info
        return {
            "intent": intent,
            "state": session.state.value,
            "suggested_department": suggestion.department,
            "dept_reason": suggestion.reason,
            "dept_confidence": suggestion.confidence,
            "queue_info": qi,
            "response": (
                f"Dựa trên thông tin anh/chị cung cấp, hệ thống đề xuất đăng ký khám tại khoa "
                f"{suggestion.department}. Hiện có {qi['current_queue']} người đang chờ, "
                f"thời gian chờ dự kiến {qi['estimated_wait']} phút. Anh/chị xác nhận đăng ký chứ?"
            ),
        }

    def _handle_new_visit(self, session: KioskSession, llm: dict) -> dict:
        dept_names = [d["name"] for d in triage_service.list_departments()]
        llm_dept = llm.get("suggested_department")
        need_more = bool(llm.get("need_more_info", True))

        # 1) LLM quyết định khoa → ưu tiên
        if llm_dept:
            suggestion = triage_service.suggest_department(
                session.symptoms, llm_dept, valid_departments=dept_names
            )
            if suggestion:
                return self._propose_department(session, suggestion)

        # 2) LLM cho rằng còn thiếu thông tin → tôn trọng, KHÔNG ép rule
        if need_more:
            session.state = SessionState.COLLECTING
            return {
                "intent": "new_visit",
                "state": session.state.value,
                "response": llm.get("response") or "Anh/chị vui lòng mô tả thêm triệu chứng để tôi hỗ trợ chính xác hơn.",
            }

        # 3) Fallback rule-based: LLM không đề xuất khoa và cho rằng đủ thông tin
        suggestion = triage_service.suggest_department(
            session.symptoms, None, valid_departments=dept_names
        )
        if suggestion:
            return self._propose_department(session, suggestion)

        session.state = SessionState.COLLECTING
        return {
            "intent": "new_visit",
            "state": session.state.value,
            "response": llm.get("response") or "Anh/chị vui lòng mô tả thêm triệu chứng để tôi hỗ trợ chính xác hơn.",
        }

    def _handle_other(self, session: KioskSession, llm: dict) -> dict:
        intent = llm.get("intent", "support")
        return {
            "intent": intent,
            "state": session.state.value,
            "response": llm.get("response") or "Tôi sẽ hỗ trợ anh/chị ngay.",
            "departments": triage_service.list_departments(),
        }

    # ── 6. Đăng ký / Thanh toán / Cấp số ────────────────
    def _start_registration(self, session: KioskSession) -> dict:
        """Bệnh nhân xác nhận đề xuất khoa → tính phí → thanh toán/xác nhận."""
        if not session.suggested_department:
            return {"error": "Chưa có khoa được đề xuất"}

        session.queue_info = triage_service.get_queue_info(session.suggested_department)
        payment = triage_service.estimate_payment(
            session.patient_id or 0, session.insurance_valid
        )
        session.payment = payment

        if payment.get("patient_pay", 0) > 0:
            session.state = SessionState.PAYMENT
            return {
                "intent": "payment",
                "state": session.state.value,
                "payment": payment,
                "response": (
                    f"Phí đăng ký khám là {payment['amount']:,.0f} đồng. "
                    f"BHYT chi trả {payment['insurance_covered']:,.0f} đồng, anh/chị cần thanh toán "
                    f"{payment['patient_pay']:,.0f} đồng. Anh/chị xác nhận thanh toán chứ?"
                ),
            }

        session.state = SessionState.CONFIRMING
        return {
            "intent": "confirm",
            "state": session.state.value,
            "payment": payment,
            "suggested_department": session.suggested_department,
            "queue_info": session.queue_info,
            "response": (
                f"Anh/chị xác nhận đăng ký khám tại khoa {session.suggested_department} "
                f"và cấp số thứ tự chứ?"
            ),
        }

    def process_payment(self, session_id: str, method: str = "mock") -> dict:
        session = self.get_session(session_id)
        if not session or not session.payment:
            return {"error": "Không có giao dịch thanh toán"}
        payment_id = session.payment.get("payment_id")
        result = get_payment_adapter().process_payment(payment_id, method)
        session.payment = result.__dict__
        session.state = SessionState.CONFIRMING
        return {
            "intent": "payment",
            "state": session.state.value,
            "payment": session.payment,
            "suggested_department": session.suggested_department,
            "queue_info": session.queue_info,
            "response": (
                f"Đã ghi nhận thanh toán. Anh/chị xác nhận đăng ký khám tại khoa "
                f"{session.suggested_department} và cấp số thứ tự chứ?"
            ),
        }

    def confirm_and_issue(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session or not session.suggested_department:
            return {"error": "Chưa có khoa được đề xuất"}

        ticket = triage_service.issue_ticket(
            session.patient_id or 0, session.suggested_department
        )
        if "error" in ticket:
            return {"error": ticket["error"]}

        session.ticket = ticket
        session.state = SessionState.DONE
        self._save_conversation(session, session.intent or "new_visit")

        return {
            "intent": "issued",
            "state": session.state.value,
            "ticket": ticket,
            "suggested_department": session.suggested_department,
            "response": (
                f"Đã cấp số thứ tự {ticket['ticket_number']} tại khoa {ticket['department']}. "
                f"Anh/chị vui lòng đến {ticket.get('location', '')} và chờ đến lượt."
            ),
        }

    def select_department(self, session_id: str, department: str) -> dict:
        """Fallback: bệnh nhân tự chọn khoa (touch)."""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session không tồn tại"}
        valid = {d["name"] for d in triage_service.list_departments()}
        if department not in valid:
            return {"error": "Khoa không hợp lệ"}

        session.suggested_department = department
        session.dept_reason = "Bệnh nhân tự chọn"
        session.dept_confidence = 1.0
        session.state = SessionState.TRIAGING
        session.queue_info = triage_service.get_queue_info(department)
        qi = session.queue_info
        return {
            "intent": "select_department",
            "state": session.state.value,
            "suggested_department": department,
            "queue_info": qi,
            "response": (
                f"Anh/chị chọn khoa {department}. Hiện có {qi['current_queue']} người đang chờ, "
                f"thời gian chờ {qi['estimated_wait']} phút. Xác nhận đăng ký chứ?"
            ),
        }

    # ── 7. Quản lý session ──────────────────────────────
    def get_session(self, session_id: str) -> Optional[KioskSession]:
        self.cleanup_expired()
        return self.sessions.get(session_id)

    def end_session(self, session_id: str):
        session = self.sessions.pop(session_id, None)
        llm_service.reset_session(session_id)
        if session:
            self._save_conversation(session, session.intent or "ended")

    def cleanup_expired(self):
        timeout = timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        now = datetime.now()
        expired = [
            sid for sid, s in self.sessions.items()
            if now - s.updated_at > timeout
        ]
        for sid in expired:
            self.end_session(sid)

    # ── Helpers ─────────────────────────────────────────
    @staticmethod
    def _merge(existing: list[str], incoming: list[str]) -> list[str]:
        seen = set(existing)
        for item in incoming:
            if item and item not in seen:
                existing.append(item)
                seen.add(item)
        return existing

    def _save_conversation(self, session: KioskSession, intent: str):
        """Lưu tóm tắt hội thoại (KHÔNG lưu PII không cần thiết)."""
        try:
            db = SessionLocal()
            transcript = " | ".join(
                f"{m['role']}: {m['text']}" for m in session.transcript
            )
            db.add(Conversation(
                session_id=session.session_id,
                intent=intent,
                transcript=transcript,
                summary=f"Đề xuất: {session.suggested_department}; Ticket: {session.ticket and session.ticket.get('ticket_number')}",
            ))
            db.commit()
        except Exception:
            pass
        finally:
            db.close()


orchestrator = KioskOrchestrator()
