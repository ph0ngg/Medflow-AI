import { useEffect } from 'react'
import { useKiosk } from './hooks/useKiosk'
import { HomeScreen } from './screens/HomeScreen'
import { FaceLoginScreen } from './screens/FaceLoginScreen'
import { RegisterScreen } from './screens/RegisterScreen'
import { MenuScreen } from './screens/MenuScreen'
import { AuthScreen } from './screens/AuthScreen'
import { ChatScreen } from './screens/ChatScreen'
import { DepartmentScreen } from './screens/DepartmentScreen'
import { DepartmentsScreen } from './screens/DepartmentsScreen'
import { PaymentScreen } from './screens/PaymentScreen'
import { ConfirmScreen } from './screens/ConfirmScreen'
import { TicketScreen } from './screens/TicketScreen'
import { EmergencyScreen } from './screens/EmergencyScreen'
import { EndScreen } from './screens/EndScreen'

// Màn hình tự reset về idle sau timeout (PRD: sau mỗi phiên phải reset)
const RESET_AFTER_MS = 25_000

export default function App() {
  const kiosk = useKiosk()

  // Auto reset khi đứng ở màn hình kết thúc/cảnh báo (chống lộ dữ liệu người trước)
  useEffect(() => {
    if (['ticket', 'end', 'emergency'].includes(kiosk.screen)) {
      const id = setTimeout(() => kiosk.reset(), RESET_AFTER_MS)
      return () => clearTimeout(id)
    }
  }, [kiosk.screen]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="app">
      <header className="app-header">
        <span className="brand">🏥 MedFlow AI</span>
        <span className="tagline">Kiosk tiếp đón thông minh</span>
      </header>

      <main className="app-main">
        {kiosk.screen === 'home' && <HomeScreen kiosk={kiosk} />}
        {kiosk.screen === 'faceLogin' && <FaceLoginScreen kiosk={kiosk} />}
        {kiosk.screen === 'register' && <RegisterScreen kiosk={kiosk} />}
        {kiosk.screen === 'menu' && <MenuScreen kiosk={kiosk} />}
        {kiosk.screen === 'auth' && <AuthScreen kiosk={kiosk} />}
        {kiosk.screen === 'chat' && <ChatScreen kiosk={kiosk} />}
        {kiosk.screen === 'department' && <DepartmentScreen kiosk={kiosk} />}
        {kiosk.screen === 'departments' && <DepartmentsScreen kiosk={kiosk} />}
        {kiosk.screen === 'payment' && <PaymentScreen kiosk={kiosk} />}
        {kiosk.screen === 'confirm' && <ConfirmScreen kiosk={kiosk} />}
        {kiosk.screen === 'ticket' && <TicketScreen kiosk={kiosk} />}
        {kiosk.screen === 'emergency' && <EmergencyScreen kiosk={kiosk} />}
        {kiosk.screen === 'end' && <EndScreen kiosk={kiosk} />}
      </main>

      <footer className="app-footer">
        MedFlow AI v2.0 — Bản thử nghiệm · Không thay thế chẩn đoán y khoa
      </footer>
    </div>
  )
}
