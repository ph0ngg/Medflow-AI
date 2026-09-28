import { BigButton, Card, QueueInfoCard } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 07+08+09. Tóm tắt nhu cầu + Đề xuất khoa + Hàng đợi. */
export function DepartmentScreen({ kiosk }: { kiosk: Kiosk }) {
  return (
    <div className="screen dept">
      <h1>Đề xuất khoa khám</h1>

      <Card className="summary-card">
        <h3>Tóm tắt nhu cầu</h3>
        {kiosk.messages.length > 0 && (
          <p className="summary-line">{kiosk.messages[kiosk.messages.length - 1].text}</p>
        )}
        {kiosk.suggestedDept && (
          <div className="dept-proposal">
            <span className="dept-name">🏥 {kiosk.suggestedDept}</span>
            {kiosk.deptReason && <span className="dept-reason">{kiosk.deptReason}</span>}
          </div>
        )}
      </Card>

      {kiosk.queueInfo && <QueueInfoCard qi={kiosk.queueInfo} />}

      <p className="disclaimer">
        ⚕️ Đây chỉ là gợi ý hỗ trợ tiếp đón, không phải chẩn đoán y khoa.
      </p>

      <div className="stack">
        <BigButton onClick={() => kiosk.sendText('có')}>✅ Xác nhận đăng ký</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.goToDepartments()}>🔀 Chọn khoa khác</BigButton>
        <BigButton variant="danger" onClick={kiosk.reset}>🆘 Gọi nhân viên</BigButton>
      </div>
    </div>
  )
}
