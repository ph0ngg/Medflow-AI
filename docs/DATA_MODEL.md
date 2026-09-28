# DATA MODEL — MedFlow AI (ERD + seed)

## Entities (SQLAlchemy, `backend/app/db/models.py`)

```mermaid
erDiagram
    PATIENT ||--o| INSURANCE : "có"
    PATIENT ||--o{ APPOINTMENT : "có"
    PATIENT ||--o{ VISITHISTORY : "có"
    PATIENT ||--o{ QUEUETICKET : "nhận"
    PATIENT ||--o{ PAYMENT : "trả"
    DEPARTMENT ||--o{ QUEUETICKET : "phục vụ"
    PATIENT ||--o{ CONVERSATION : "phiên"

    PATIENT { int id PK; string full_name; string dob; string cccd UK; string phone; string face_id; int is_returning }
    INSURANCE { int id PK; int patient_id FK; string bhyt_code UK; string status; int coverage_percent }
    APPOINTMENT { int id PK; int patient_id FK; string department; string appointment_date; string status }
    VISITHISTORY { int id PK; int patient_id FK; string department; string visit_date; string doctor_name; string notes }
    DEPARTMENT { int id PK; string name UK; string location; int current_queue; int estimated_wait }
    QUEUETICKET { int id PK; int patient_id FK; int department_id FK; int ticket_number; string status }
    CONVERSATION { int id PK; string session_id; string intent; text transcript; text summary }
    PAYMENT { int id PK; int patient_id FK; int ticket_id FK; float amount; float insurance_covered; float patient_pay; string status }
```

## Enum giá trị
- `Appointment.status`: `scheduled | checked_in | cancelled | completed`
- `QueueTicket.status`: `waiting | serving | done | cancelled`
- `Insurance.status`: `active | expired | invalid`
- `Payment.status`: `pending | paid | failed`

## Seed data (`backend/app/db/seed.py`)
- **8 khoa**: Nội tiêu hóa, Nội tim mạch, Nội hô hấp, Nội tiết, Cơ xương khớp, Da liễu, Tai Mũi Họng, Mắt.
- **3 bệnh nhân**: Nguyễn Văn A (có BHYT + lịch hẹn Nội tiết), Trần Thị B (BHYT + lịch hẹn Tim mạch), Lê Văn C (mới, không BHYT).

## Ghi chú
- `face_id` liên kết với FAISS (`backend/ai_modules/faiss/id2name.json`).
- Prototype dùng SQLite (`MEDFLOW_DB_URL`); production thay engine qua adapter.
