import { BigButton } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 14. Cảnh báo — red flag, không cấp số thông thường. */
export function EmergencyScreen({ kiosk }: { kiosk: Kiosk }) {
  return (
    <div className="screen emergency">
      <div className="emergency-box">
        <div className="emergency-icon">⚠️</div>
        <h1>Cần hỗ trợ y tế ngay</h1>
        <p>
          Các triệu chứng anh/chị cung cấp có thể cần được nhân viên y tế đánh giá ngay.
        </p>
        <p className="emergency-guide">
          Vui lòng liên hệ <strong>nhân viên y tế gần nhất</strong> hoặc đến khu vực cấp cứu.
        </p>
        <BigButton variant="danger" onClick={kiosk.reset}>Đã hiểu</BigButton>
      </div>
    </div>
  )
}
