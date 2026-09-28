import { BigButton, Card } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

function maskCccd(cccd?: string): string {
  if (!cccd) return '—'
  return cccd.slice(0, 4) + '••••••' + cccd.slice(-2)
}

function maskBhyt(code?: string): string {
  if (!code) return '—'
  return code.slice(0, 3) + '••••••' + code.slice(-3)
}

/** 04. Hồ sơ bệnh nhân — xác nhận thông tin + BHYT + lịch hẹn. */
export function ProfileScreen({ kiosk }: { kiosk: Kiosk }) {
  const { profile, patientName, isReturning } = kiosk

  return (
    <div className="screen profile">
      <h1>{isReturning ? 'Xin chào' : 'Xác nhận hồ sơ'}</h1>
      <h2 className="profile-name">{patientName || profile?.full_name}</h2>

      <Card>
        <div className="kv">
          <span>Ngày sinh</span><strong>{profile?.dob || '—'}</strong>
        </div>
        <div className="kv">
          <span>CCCD</span><strong>{maskCccd(profile?.cccd)}</strong>
        </div>
        <div className="kv">
          <span>BHYT</span>
          <strong>{profile?.bhyt_code ? maskBhyt(profile.bhyt_code) : 'Chưa có'}</strong>
        </div>
        <div className="kv">
          <span>Trạng thái BHYT</span>
          <strong className={profile?.insurance_valid ? 'ok' : 'warn'}>
            {profile?.insurance_valid ? '✅ Hợp lệ' : '⚠️ Chưa xác minh'}
          </strong>
        </div>
      </Card>

      {profile?.upcoming_appointments && profile.upcoming_appointments.length > 0 && (
        <Card>
          <h3>📅 Lịch hẹn sắp tới</h3>
          {profile.upcoming_appointments.map((a) => (
            <div key={a.id} className="kv">
              <span>{a.department}</span>
              <strong>{a.appointment_date} {a.appointment_time || ''}</strong>
            </div>
          ))}
        </Card>
      )}

      {profile?.last_department && (
        <Card>
          <div className="kv">
            <span>Khoa khám gần nhất</span><strong>{profile.last_department}</strong>
          </div>
        </Card>
      )}

      <div className="stack">
        <BigButton onClick={() => kiosk.goToDepartments()}>🏥 Chọn phòng khám</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.sendText('Tôi có lịch hẹn')}>📅 Khám theo lịch hẹn</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.sendText('Tôi muốn tái khám')}>🔄 Tái khám</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.sendText('Tôi có triệu chứng mới')}>🩺 Triệu chứng mới</BigButton>
      </div>
    </div>
  )
}
