import { BigButton, Card, QueueInfoCard, formatVnd } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 11. Xác nhận đăng ký cuối cùng trước khi cấp số. */
export function ConfirmScreen({ kiosk }: { kiosk: Kiosk }) {
  const p = kiosk.payment
  return (
    <div className="screen confirm">
      <h1>Xác nhận đăng ký</h1>
      <Card>
        <div className="kv"><span>Bệnh nhân</span><strong>{kiosk.patientName || '—'}</strong></div>
        <div className="kv"><span>Khoa khám</span><strong>{kiosk.suggestedDept || '—'}</strong></div>
        {p && <div className="kv"><span>Phí</span><strong>{formatVnd(p.patient_pay)}</strong></div>}
      </Card>

      {kiosk.queueInfo && <QueueInfoCard qi={kiosk.queueInfo} />}

      <div className="stack">
        <BigButton onClick={() => kiosk.doConfirm()}>✅ Xác nhận & cấp số</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.sendText('không')}>Quay lại</BigButton>
      </div>
    </div>
  )
}
