import { useEffect } from 'react'
import { BigButton, Spinner } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** Chọn phòng khám thủ công — luồng chính kiểu kiosk truyền thống. */
export function DepartmentsScreen({ kiosk }: { kiosk: Kiosk }) {
  useEffect(() => {
    if (kiosk.departments.length === 0) void kiosk.loadDepartments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="screen depts">
      <h1>Chọn phòng khám</h1>
      <p className="sub">
        Chạm vào khoa/phòng khám bạn cần để lấy số. Chatbot tư vấn chỉ là lựa chọn phụ.
      </p>

      <div className="dept-list">
        {kiosk.departments.length === 0 && <Spinner label="Đang tải danh sách khoa..." />}
        {kiosk.departments.map((d) => (
          <button
            key={d.id}
            className="dept-option"
            onClick={() => kiosk.chooseDepartment(d.name)}
          >
            <span className="dept-option-main">
              <strong>{d.name}</strong>
              <small>{d.location || '—'}</small>
            </span>
            <span className="dept-option-meta">
              👥 {d.current_queue} · ⏱️ {d.estimated_wait} phút
            </span>
          </button>
        ))}
      </div>

      <div className="exit-row">
        <BigButton variant="secondary" onClick={kiosk.reset}>↩️ Quay lại</BigButton>
        <BigButton variant="danger" onClick={kiosk.reset}>🆘 Gọi nhân viên</BigButton>
      </div>
    </div>
  )
}
