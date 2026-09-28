"""
Data model — MedFlow AI (SQLAlchemy 2.0).

Ánh xạ theo PRD mục 10.1 (Dữ liệu prototype):
Patient, Insurance, Appointment, VisitHistory, Department,
Queue, Conversation, Ticket, Payment.

Đây là dữ liệu prototype; tích hợp thật sẽ đi qua adapter layer.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import DATABASE_URL

Base = declarative_base()


# ── Bệnh nhân ────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False)
    dob = Column(String(10))                        # DD/MM/YYYY
    cccd = Column(String(12), unique=True, index=True)
    phone = Column(String(20))
    address = Column(String(200))                   # Quê quán / địa chỉ
    face_id = Column(String(50))                    # id trong FAISS (nếu đã đăng ký khuôn mặt)
    is_returning = Column(Integer, default=0)       # 0=mới, 1=cũ
    created_at = Column(DateTime, default=datetime.now)

    insurance = relationship("Insurance", back_populates="patient", uselist=False)
    appointments = relationship("Appointment", back_populates="patient")
    histories = relationship("VisitHistory", back_populates="patient")


# ── BHYT ────────────────────────────────────────────────
class Insurance(Base):
    __tablename__ = "insurances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True)
    bhyt_code = Column(String(15), unique=True)
    status = Column(String(20), default="active")   # active | expired | invalid
    valid_from = Column(String(10))
    valid_to = Column(String(10))
    coverage_percent = Column(Integer, default=80)

    patient = relationship("Patient", back_populates="insurance")


# ── Lịch hẹn ─────────────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    department = Column(String(100))
    appointment_date = Column(String(10))           # DD/MM/YYYY
    appointment_time = Column(String(10))           # HH:MM
    status = Column(String(20), default="scheduled")  # scheduled | checked_in | cancelled | completed

    patient = relationship("Patient", back_populates="appointments")


# ── Lịch sử khám ─────────────────────────────────────────
class VisitHistory(Base):
    __tablename__ = "visit_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    department = Column(String(100))
    visit_date = Column(String(10))
    doctor_name = Column(String(200))
    notes = Column(String(500))

    patient = relationship("Patient", back_populates="histories")


# ── Khoa ──────────────────────────────────────────────────
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True)
    location = Column(String(100), default="")      # Tầng/Phòng — hỗ trợ wayfinding
    services = Column(String(500), default="")      # Mô tả dịch vụ ngắn
    current_queue = Column(Integer, default=0)      # Số người đang chờ
    estimated_wait = Column(Integer, default=15)    # Thời gian chờ dự kiến (phút)
    is_active = Column(Integer, default=1)


# ── Số thứ tự / Hàng đợi ─────────────────────────────────
class QueueTicket(Base):
    __tablename__ = "queue_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    ticket_number = Column(Integer)
    status = Column(String(20), default="waiting")  # waiting | serving | done | cancelled
    created_at = Column(DateTime, default=datetime.now)

    department = relationship("Department")


# ── Hội thoại ────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), index=True)
    intent = Column(String(30))
    transcript = Column(Text)                       # Tóm tắt cần thiết, KHÔNG lưu PII không cần thiết
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


# ── Thanh toán ───────────────────────────────────────────
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    ticket_id = Column(Integer, ForeignKey("queue_tickets.id"), nullable=True)
    amount = Column(Float, default=0)               # Tổng phí
    insurance_covered = Column(Float, default=0)    # BHYT chi trả
    patient_pay = Column(Float, default=0)          # Người bệnh trả
    method = Column(String(20), default="mock")     # mock | cash | card | qr
    status = Column(String(20), default="pending")  # pending | paid | failed
    created_at = Column(DateTime, default=datetime.now)


# ── Engine / Session ─────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Tạo tất cả bảng nếu chưa tồn tại + migration nhẹ."""
    Base.metadata.create_all(engine)
    _migrate()


def _migrate():
    """Migration nhẹ cho SQLite prototype: thêm cột mới nếu thiếu.

    `create_all` KHÔNG sửa bảng đã tồn tại, nên các cột thêm sau này
    phải được ALTER TABLE thủ công ở đây (idempotent).
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "patients" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("patients")}
        if "address" not in existing_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE patients ADD COLUMN address VARCHAR(200)"))


def get_db():
    """FastAPI dependency: yield một DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
