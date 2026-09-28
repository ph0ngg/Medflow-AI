import { BigButton } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 15. Kết thúc phiên — tự reset về màn hình chờ. */
export function EndScreen({ kiosk }: { kiosk: Kiosk }) {
  return (
    <div className="screen end">
      <h1>👋 Cảm ơn anh/chị đã sử dụng MedFlow AI</h1>
      <p>Phiên giao dịch đã kết thúc. Dữ liệu hiển thị sẽ được xóa.</p>
      <BigButton onClick={kiosk.reset}>🔄 Phiên mới</BigButton>
    </div>
  )
}
