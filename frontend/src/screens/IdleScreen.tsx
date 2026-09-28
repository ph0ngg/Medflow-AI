import { useRef } from 'react'
import { CameraFeed, type CameraFeedHandle } from '../components/CameraFeed'
import { BigButton } from '../components/ui'
import type { Face } from '../types'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 01. Màn hình chờ — voice-first + touch fallback. */
export function IdleScreen({ kiosk }: { kiosk: Kiosk }) {
  const camRef = useRef<CameraFeedHandle>(null)
  const startedRef = useRef(false)

  const onDetect = (faces: Face[]) => {
    if (startedRef.current) return
    const known = faces.find((f) => f.name)
    if (known) {
      startedRef.current = true
      void kiosk.startWithFace(known.name, known.id)
    }
    // Khuôn mặt lạ → chờ bệnh nhân chạm "Xác thực" hoặc tự bắt đầu sau
  }

  return (
    <div className="screen idle">
      <div className="idle-hero">
        <div className="logo">🏥 MedFlow AI</div>
        <h1 className="idle-title">Nói với tôi điều anh/chị cần</h1>
        <p className="idle-sub">Chạm vào nút bên dưới hoặc đứng trước camera để bắt đầu</p>
      </div>

      <CameraFeed ref={camRef} autoDetect onDetect={onDetect} />

      <div className="idle-actions">
        <BigButton onClick={() => kiosk.goToDepartments()}>🏥 Chọn phòng khám</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.startNew()}>💬 Tư vấn bằng AI (nói nhu cầu)</BigButton>
        <BigButton variant="secondary" onClick={() => kiosk.startNew()}>🪪 Xác thực danh tính</BigButton>
      </div>
    </div>
  )
}
