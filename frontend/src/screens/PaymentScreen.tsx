import { BigButton, Card, formatVnd } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 10. Thanh toán (mock). */
export function PaymentScreen({ kiosk }: { kiosk: Kiosk }) {
  const p = kiosk.payment
  return (
    <div className="screen payment">
      <h1>Thanh toán</h1>
      <Card>
        <div className="kv"><span>Tổng phí khám</span><strong>{formatVnd(p?.amount)}</strong></div>
        <div className="kv"><span>BHYT chi trả</span><strong>{formatVnd(p?.insurance_covered)}</strong></div>
        <div className="kv big"><span>Cần thanh toán</span><strong>{formatVnd(p?.patient_pay)}</strong></div>
      </Card>

      <div className="stack">
        <BigButton onClick={() => kiosk.doPay()}>💳 Thanh toán (mô phỏng)</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.sendText('không')}>
          Bỏ qua — thanh toán tại quầy
        </BigButton>
      </div>
    </div>
  )
}
