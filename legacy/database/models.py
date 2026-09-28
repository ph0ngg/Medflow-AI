"""
Các model dữ liệu (SQLAlchemy) cho MedFlow AI.
Mô phỏng dữ liệu bệnh nhân, lịch hẹn, lịch sử khám, hàng đợi.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from config import DATABASE_URL

Base = declarative_base()


# ── Bệnh nhân ────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False)
    dob = Column(String(10))                        # DD/MM/YYYY
    cccd = Column(String(12), unique=True)          # Căn cước công dân
    bhyt_code = Column(String(15))                  # Mã BHYT
    face_embedding = Column(String)                 # JSON string của embedding (lưu tạm, thực tế dùng FAISS)
    face_image_path = Column(String)                # Đường dẫn ảnh khuôn mặt đã đăng ký
    is_returning = Column(Integer, default=0)       # 0=mới, 1=cũ
    created_at = Column(DateTime, default=datetime.now)

    appointments = relationship("Appointment", back_populates="patient")
    histories = relationship("MedicalHistory", back_populates="patient")


# ── Lịch hẹn ─────────────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    department = Column(String(100))
    appointment_date = Column(String(10))           # DD/MM/YYYY
    status = Column(String(20), default="scheduled")  # scheduled | checked_in | cancelled

    patient = relationship("Patient", back_populates="appointments")


# ── Lịch sử khám ─────────────────────────────────────────
class MedicalHistory(Base):
    __tablename__ = "medical_history"

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
    current_queue = Column(Integer, default=0)      # Số người đang chờ
    estimated_wait = Column(Integer, default=15)    # Thời gian chờ ước tính (phút)
    is_active = Column(Integer, default=1)


# ── Hàng đợi / Số thứ tự ─────────────────────────────────
class QueueTicket(Base):
    __tablename__ = "queue_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    ticket_number = Column(Integer)
    status = Column(String(20), default="waiting")  # waiting | serving | done
    created_at = Column(DateTime, default=datetime.now)


# ── Khởi tạo DB ───────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Tạo tất cả bảng nếu chưa tồn tại."""
    Base.metadata.create_all(engine)

def get_db():
    """Yield một database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
