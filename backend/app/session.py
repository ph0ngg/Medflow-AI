"""
Session state — MedFlow AI.

Định nghĩa trạng thái phiên giao dịch tại kiosk (state machine)
theo PRD mục 6 (Luồng trải nghiệm người dùng).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SessionState(str, Enum):
    IDLE = "idle"                    # Chờ bệnh nhân
    DETECTING = "detecting"          # Đang phát hiện khuôn mặt
    IDENTIFYING = "identifying"      # Đang xác thực danh tính (face/cccd)
    AUTH_CCCD = "auth_cccd"          # Xác thực qua CCCD
    PROFILE_REVIEW = "profile_review"  # Xem/xác nhận hồ sơ
    GREETING = "greeting"            # Chào hỏi bệnh nhân cũ
    COLLECTING = "collecting"        # Thu thập nhu cầu/triệu chứng
    TRIAGING = "triaging"            # Đã có đề xuất khoa, chờ xác nhận
    QUEUE_REVIEW = "queue_review"    # Xem hàng đợi
    PAYMENT = "payment"              # Thanh toán
    CONFIRMING = "confirming"        # Xác nhận đăng ký cuối cùng
    ISSUING = "issuing"              # Đang cấp số
    EMERGENCY = "emergency"          # Cảnh báo khẩn cấp
    DONE = "done"                    # Hoàn tất


@dataclass
class KioskSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: SessionState = SessionState.IDLE

    # Định danh
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    is_returning: bool = False
    identity_method: Optional[str] = None      # face | cccd | code
    cccd: Optional[str] = None
    bhyt_code: Optional[str] = None
    insurance_valid: bool = False
    insurance_status: Optional[str] = None

    # Hội thoại & phân luồng
    symptoms: list[str] = field(default_factory=list)
    transcript: list[dict] = field(default_factory=list)
    intent: Optional[str] = None
    suggested_department: Optional[str] = None
    dept_reason: Optional[str] = None
    dept_confidence: Optional[float] = None
    queue_info: Optional[dict] = None

    # Thanh toán & cấp số
    payment: Optional[dict] = None
    ticket: Optional[dict] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def touch(self):
        self.updated_at = datetime.now()

    def add_message(self, role: str, text: str):
        self.transcript.append({"role": role, "text": text})
        self.touch()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "is_returning": self.is_returning,
            "identity_method": self.identity_method,
            "cccd": self.cccd,
            "bhyt_code": self.bhyt_code,
            "insurance_valid": self.insurance_valid,
            "insurance_status": self.insurance_status,
            "symptoms": self.symptoms,
            "intent": self.intent,
            "suggested_department": self.suggested_department,
            "dept_reason": self.dept_reason,
            "dept_confidence": self.dept_confidence,
            "queue_info": self.queue_info,
            "payment": self.payment,
            "ticket": self.ticket,
        }
