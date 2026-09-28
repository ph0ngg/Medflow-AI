import { useRef, useState } from 'react'
import { CameraFeed, type CameraFeedHandle } from '../components/CameraFeed'
import { BigButton, Card, Spinner } from '../components/ui'
import { scanCccd } from '../api'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 03. Xác thực danh tính — CCCD / mã bệnh nhân (fallback khi không nhận diện mặt). */
export function AuthScreen({ kiosk }: { kiosk: Kiosk }) {
  const [cccd, setCccd] = useState('')
  const [code, setCode] = useState('')
  const [mode, setMode] = useState<'cccd' | 'code'>('cccd')
  const [scanning, setScanning] = useState(false)
  const camRef = useRef<CameraFeedHandle>(null)

  const doScan = async () => {
    setScanning(true)
    try {
      const blob = await camRef.current?.capture()
      if (!blob) return
      const res = await scanCccd(blob)
      const info = res?.info
      if (info?.cccd) {
        setCccd(info.cccd)
        await kiosk.verifyCccd(info.cccd)
      } else {
        setCccd('')
      }
    } catch (e: any) {
      // show nothing; keep simple
    } finally {
      setScanning(false)
    }
  }

  const submit = () => {
    if (mode === 'cccd' && cccd.trim()) void kiosk.verifyCccd(cccd.trim())
    else if (mode === 'code' && code.trim()) void kiosk.verifyCccd(undefined, code.trim())
  }

  return (
    <div className="screen auth">
      <h1>Xác thực danh tính</h1>
      <p className="sub">Vui lòng quét CCCD hoặc nhập mã bệnh nhân để tiếp tục.</p>

      <CameraFeed ref={camRef} />

      <Card className="auth-box">
        <div className="tabs">
          <button className={mode === 'cccd' ? 'tab active' : 'tab'} onClick={() => setMode('cccd')}>CCCD</button>
          <button className={mode === 'code' ? 'tab active' : 'tab'} onClick={() => setMode('code')}>Mã bệnh nhân</button>
        </div>

        {mode === 'cccd' ? (
          <>
            <input
              className="big-input"
              placeholder="Nhập 12 số CCCD"
              value={cccd}
              maxLength={12}
              inputMode="numeric"
              onChange={(e) => setCccd(e.target.value.replace(/\D/g, ''))}
            />
            <div className="row">
              <BigButton onClick={doScan} disabled={scanning}>
                {scanning ? <Spinner label="Đang quét..." /> : '📷 Quét CCCD'}
              </BigButton>
              <BigButton variant="secondary" onClick={submit} disabled={!cccd.trim()}>Xác nhận</BigButton>
            </div>
          </>
        ) : (
          <>
            <input
              className="big-input"
              placeholder="Nhập mã bệnh nhân"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <BigButton onClick={submit} disabled={!code.trim()}>Xác nhận</BigButton>
          </>
        )}
      </Card>

      <div className="exit-row">
        <BigButton variant="secondary" onClick={kiosk.reset}>↩️ Quay lại</BigButton>
        <BigButton variant="danger" onClick={kiosk.reset}>🆘 Gọi nhân viên</BigButton>
      </div>
    </div>
  )
}
