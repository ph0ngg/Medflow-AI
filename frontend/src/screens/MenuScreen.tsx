import { BigButton, Card } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** Sau đăng nhập: chọn khoa khám hoặc chatbot AI. */
export function MenuScreen({ kiosk }: { kiosk: Kiosk }) {
  return (
    <div className="screen menu">
      <div className="idle-hero">
        <h1>Xin chào, {kiosk.patientName || 'anh/chị'}!</h1>
        <p className="idle-sub">Anh/chị muốn làm gì hôm nay?</p>
      </div>

      {kiosk.profile && (
        <Card>
          {kiosk.profile.dob && (
            <div className="kv"><span>Ngày sinh</span><strong>{kiosk.profile.dob}</strong></div>
          )}
          {kiosk.profile.address && (
            <div className="kv"><span>Quê quán</span><strong>{kiosk.profile.address}</strong></div>
          )}
          {kiosk.profile.bhyt_code && (
            <div className="kv">
              <span>BHYT</span>
              <strong className={kiosk.profile.insurance_valid ? 'ok' : 'warn'}>
                {kiosk.profile.insurance_valid ? '✅ Hợp lệ' : '⚠️ Chưa xác minh'}
              </strong>
            </div>
          )}
        </Card>
      )}

      <div className="stack">
        <BigButton onClick={() => kiosk.goToDepartments()}>🏥 Chọn khoa khám</BigButton>
        <BigButton variant="secondary" onClick={kiosk.goToChat}>💬 Tư vấn bằng AI (chatbot)</BigButton>
      </div>

      <BigButton variant="secondary" onClick={kiosk.reset}>🚪 Đăng xuất</BigButton>
    </div>
  )
}
