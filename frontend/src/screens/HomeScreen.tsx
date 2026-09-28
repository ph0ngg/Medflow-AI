import { BigButton } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** Màn hình đầu: Đăng nhập / Đăng ký. */
export function HomeScreen({ kiosk }: { kiosk: Kiosk }) {
  return (
    <div className="screen home">
      <div className="idle-hero">
        <div className="logo">🏥 MedFlow AI</div>
        <h1>Chào mừng đến với MedFlow AI</h1>
        <p className="idle-sub">Vui lòng đăng nhập hoặc đăng ký tài khoản để tiếp tục</p>
      </div>

      <div className="stack">
        <BigButton onClick={kiosk.goToFaceLogin}>👤 Đăng nhập bằng khuôn mặt</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.goToAuth()}>🪪 Đăng nhập bằng CCCD / mã bệnh nhân</BigButton>
        <BigButton variant="secondary" onClick={kiosk.goToRegister}>📝 Đăng ký mới</BigButton>
      </div>
    </div>
  )
}
