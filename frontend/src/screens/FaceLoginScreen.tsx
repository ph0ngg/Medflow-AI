import { useRef, useState } from 'react'
import { CameraFeed, type CameraFeedHandle } from '../components/CameraFeed'
import { BigButton, Spinner } from '../components/ui'
import { detectFace } from '../api'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** Đăng nhập bằng khuôn mặt (chỉ nhận diện khi bấm nút, không tự động). */
export function FaceLoginScreen({ kiosk }: { kiosk: Kiosk }) {
  const camRef = useRef<CameraFeedHandle>(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const scan = async () => {
    setBusy(true)
    setStatus('Đang nhận diện...')
    try {
      const blob = await camRef.current?.capture()
      if (!blob) {
        setStatus('Không lấy được ảnh từ camera. Vui lòng thử lại.')
        return
      }
      const res = await detectFace(blob)
      if (res?.detected && res.faces?.length) {
        const face = res.faces[0]
        if (face.name) {
          setStatus(`✅ Nhận diện thành công: ${face.name}`)
          await kiosk.startWithFace(face.name, face.id)
        } else {
          setStatus('Không nhận diện được khuôn mặt. Vui lòng thử lại hoặc đăng ký mới.')
        }
      } else {
        setStatus('Không phát hiện khuôn mặt. Vui lòng nhìn thẳng vào camera.')
      }
    } catch {
      setStatus('Lỗi kết nối máy chủ. Vui lòng thử lại.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen face-login">
      <h1>Đăng nhập bằng khuôn mặt</h1>
      <p className="sub">Vui lòng nhìn thẳng vào camera rồi bấm "Nhận diện".</p>

      <CameraFeed ref={camRef} />

      {status && <div className="status-bar">{status}</div>}

      <div className="stack">
        <BigButton onClick={scan} disabled={busy}>
          {busy ? <Spinner label="Đang nhận diện..." /> : '📷 Nhận diện khuôn mặt'}
        </BigButton>
        <BigButton variant="secondary" onClick={kiosk.goToRegister}>📝 Chưa có tài khoản? Đăng ký mới</BigButton>
        <BigButton variant="secondary" onClick={kiosk.goHome}>↩️ Quay lại</BigButton>
      </div>
    </div>
  )
}
