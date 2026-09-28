"""
Mock Payment Adapter — mô phỏng cổng thanh toán.
Luôn thành công (demo). Khi có cổng thanh toán thật, thay adapter này.
"""
from app.adapters.base import PaymentResult
from app.db.models import SessionLocal, Payment


class MockPaymentAdapter:
    def create_payment(self, patient_id: int, amount: float, insurance_covered: float) -> PaymentResult:
        patient_pay = max(0.0, amount - insurance_covered)
        db = SessionLocal()
        try:
            payment = Payment(
                patient_id=patient_id,
                amount=amount,
                insurance_covered=insurance_covered,
                patient_pay=patient_pay,
                method="mock",
                status="pending",
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return PaymentResult(
                amount=amount,
                insurance_covered=insurance_covered,
                patient_pay=patient_pay,
                status="pending",
                method="mock",
                payment_id=payment.id,
            )
        finally:
            db.close()

    def process_payment(self, payment_id: int, method: str = "mock") -> PaymentResult:
        db = SessionLocal()
        try:
            payment = db.query(Payment).filter_by(id=payment_id).first()
            if not payment:
                return PaymentResult(status="failed")
            payment.status = "paid"
            payment.method = method
            db.commit()
            return PaymentResult(
                amount=payment.amount,
                insurance_covered=payment.insurance_covered,
                patient_pay=payment.patient_pay,
                status="paid",
                method=method,
                payment_id=payment.id,
            )
        finally:
            db.close()
