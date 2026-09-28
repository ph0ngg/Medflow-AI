import { useRef, useState } from 'react'
import { CameraFeed, type CameraFeedHandle } from '../components/CameraFeed'
import { BigButton, Card } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** Đăng ký bệnh nhân mới. Bắt buộc: họ tên, ngày sinh, (CCCD hoặc BHYT). */
export function RegisterScreen({ kiosk }: { kiosk: Kiosk }) {
  const [form, setForm] = useState({
    full_name: '', dob: '', address: '', phone: '', cccd: '', bhyt_code: '',
  })
  const [err, setErr] = useState('')
  const [faceImage, setFaceImage] = useState<Blob | null>(null)
  const [faceStatus, setFaceStatus] = useState('')
  const camRef = useRef<CameraFeedHandle>(null)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const captureFace = async () => {
    setFaceStatus('Đang chụp...')
    const blob = await camRef.current?.capture()
    if (blob) {
      setFaceImage(blob)
      setFaceStatus('✅ Đã lưu khuôn mặt — lần sau đăng nhập chỉ cần dùng khuôn mặt')
    } else {
      setFaceStatus('⚠️ Không lấy được ảnh. Bạn vẫn có thể đăng ký không cần khuôn mặt.')
    }
  }

  const submit = async () => {
    setErr('')
    const res = await kiosk.registerPatient(form, faceImage)
    if (res?.error) setErr(res.response || 'Đăng ký thất bại.')
  }

  return (
    <div className="screen register">
      <h1>Đăng ký mới</h1>
      <p className="sub">Vui lòng điền đầy đủ thông tin (dấu * là bắt buộc).</p>

      <Card className="form-card">
        <div className="field">
          <span>Khuôn mặt (tùy chọn) — lưu để lần sau đăng nhập bằng khuôn mặt</span>
          <CameraFeed ref={camRef} />
          {faceStatus && <div className="face-status">{faceStatus}</div>}
          <BigButton variant="secondary" onClick={captureFace}>📷 Chụp khuôn mặt</BigButton>
        </div>

        <label className="field">
          <span>Họ và tên *</span>
          <input className="big-input" value={form.full_name} onChange={set('full_name')} placeholder="Nguyễn Văn A" />
        </label>
        <label className="field">
          <span>Ngày sinh *</span>
          <input className="big-input" value={form.dob} onChange={set('dob')} placeholder="DD/MM/YYYY" />
        </label>
        <label className="field">
          <span>Quê quán</span>
          <input className="big-input" value={form.address} onChange={set('address')} placeholder="Hà Nội" />
        </label>
        <label className="field">
          <span>Số điện thoại</span>
          <input className="big-input" value={form.phone} onChange={set('phone')} inputMode="tel" placeholder="090..." />
        </label>
        <label className="field">
          <span>Số CCCD (12 số) — hoặc điền BHYT bên dưới</span>
          <input className="big-input" value={form.cccd} onChange={set('cccd')} inputMode="numeric" maxLength={12} placeholder="0010..." />
        </label>
        <label className="field">
          <span>Số BHYT</span>
          <input className="big-input" value={form.bhyt_code} onChange={set('bhyt_code')} placeholder="HS..." />
        </label>

        {err && <div className="form-error">⚠️ {err}</div>}

        <BigButton onClick={submit} disabled={kiosk.busy}>
          {kiosk.busy ? 'Đang đăng ký...' : '✅ Đăng ký'}
        </BigButton>
      </Card>

      <BigButton variant="secondary" onClick={kiosk.goHome}>↩️ Quay lại</BigButton>
    </div>
  )
}
