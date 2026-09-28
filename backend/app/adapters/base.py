"""
Adapter layer — MedFlow AI.

Các hệ thống bên ngoài (HIS/EMR, BHYT, hàng đợi, thanh toán, định danh)
được tách sau interface. Prototype dùng MockAdapter; khi tích hợp thật,
chỉ cần thay adapter mà KHÔNG sửa business logic (PRD mục 11).
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


# ── DTO dùng chung ───────────────────────────────────────
@dataclass
class IdentityInfo:
    """Thông tin định danh từ nguồn được phép."""
    full_name: str = ""
    dob: str = ""
    cccd: str = ""
    address: str = ""
    phone: str = ""
    bhyt_code: str = ""
    valid: bool = False


@dataclass
class PatientRecord:
    """Hồ sơ bệnh nhân trả về từ HIS."""
    patient_id: Optional[int] = None
    full_name: str = ""
    dob: str = ""
    cccd: str = ""
    phone: str = ""
    address: str = ""
    bhyt_code: str = ""
    is_returning: bool = False
    found: bool = False


@dataclass
class InsuranceRecord:
    """Kết quả xác minh BHYT."""
    bhyt_code: str = ""
    status: str = "invalid"          # active | expired | invalid
    coverage_percent: int = 0
    valid: bool = False


@dataclass
class QueueInfo:
    department: str = ""
    current_queue: int = 0
    estimated_wait: int = 0
    now_serving: int = 0


@dataclass
class PaymentResult:
    amount: float = 0
    insurance_covered: float = 0
    patient_pay: float = 0
    status: str = "pending"          # pending | paid | failed
    method: str = "mock"
    payment_id: Optional[int] = None


# ── Interfaces (Protocol) ────────────────────────────────
class HISAdapter(Protocol):
    def get_patient_by_cccd(self, cccd: str) -> PatientRecord: ...
    def get_patient_by_code(self, code: str) -> PatientRecord: ...
    def get_appointments(self, patient_id: int) -> list[dict]: ...
    def get_visit_history(self, patient_id: int) -> list[dict]: ...
    def register_patient(self, identity: IdentityInfo) -> PatientRecord: ...
    def check_in_appointment(self, appointment_id: int) -> bool: ...


class InsuranceAdapter(Protocol):
    def verify(self, bhyt_code: str) -> InsuranceRecord: ...


class QueueAdapter(Protocol):
    def get_queue_info(self, department: str) -> QueueInfo: ...
    def issue_ticket(self, patient_id: int, department: str) -> dict: ...
    def list_departments(self) -> list[dict]: ...


class PaymentAdapter(Protocol):
    def create_payment(self, patient_id: int, amount: float, insurance_covered: float) -> PaymentResult: ...
    def process_payment(self, payment_id: int, method: str = "mock") -> PaymentResult: ...


class IdentityAdapter(Protocol):
    def verify_cccd(self, cccd: str) -> IdentityInfo: ...
