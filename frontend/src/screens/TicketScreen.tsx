import { BigButton, TicketCard, WayfindingCard } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 12+13. Cấp số + Wayfinding. */
export function TicketScreen({ kiosk }: { kiosk: Kiosk }) {
  const ticket = kiosk.ticket
  return (
    <div className="screen ticket">
      <h1>✅ Đăng ký thành công</h1>
      {ticket && (
        <TicketCard
          ticket={ticket}
          onPrint={() => window.print()}
        />
      )}
      <WayfindingCard location={ticket?.location} />
      <BigButton onClick={kiosk.reset}>🏁 Kết thúc phiên</BigButton>
    </div>
  )
}
