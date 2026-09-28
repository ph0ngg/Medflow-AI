import type { ReactNode } from 'react'
import type { QueueInfo, Ticket } from '../types'

export function BigButton({ children, onClick, variant = 'primary', disabled }: {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'danger'
  disabled?: boolean
}) {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>
}

export function StatusBar({ children }: { children: ReactNode }) {
  return <div className="status-bar">{children}</div>
}

export function Spinner({ label = 'Đang xử lý...' }: { label?: string }) {
  return <div className="spinner"><span className="spinner-dot" /> {label}</div>
}

export function formatVnd(n?: number): string {
  if (n == null) return '0'
  return n.toLocaleString('vi-VN') + ' đ'
}

export function QueueInfoCard({ qi }: { qi: QueueInfo }) {
  return (
    <div className="queue-card">
      <div className="queue-row">
        <span>👥 Đang chờ</span>
        <strong>{qi.current_queue ?? 0} người</strong>
      </div>
      <div className="queue-row">
        <span>⏱️ Chờ dự kiến</span>
        <strong>~{qi.estimated_wait ?? 0} phút</strong>
      </div>
    </div>
  )
}

export function TicketCard({ ticket, onPrint }: { ticket: Ticket; onPrint?: () => void }) {
  return (
    <div className="ticket-card">
      <div className="ticket-label">SỐ THỨ TỰ</div>
      <div className="ticket-number">#{ticket.ticket_number}</div>
      <div className="ticket-dept">📍 {ticket.department}</div>
      <div className="ticket-info">
        <div>⏱️ Chờ dự kiến: ~{ticket.estimated_wait ?? 0} phút</div>
        {ticket.location && <div>🏥 {ticket.location}</div>}
      </div>
      {onPrint && (
        <BigButton variant="secondary" onClick={onPrint}>🖨️ In phiếu</BigButton>
      )}
    </div>
  )
}

export function WayfindingCard({ location }: { location?: string }) {
  return (
    <div className="wayfinding">
      <div className="map-simple">
        <div className="map-floor">🏥 TẦNG</div>
        <div className="map-path">
          <span className="map-dot you">Bạn ở đây</span>
          <span className="map-arrow">→</span>
          <span className="map-dot dest">{location || 'Phòng khám'}</span>
        </div>
      </div>
      <p className="wayfinding-hint">
        Hãy đi theo chỉ dẫn trên màn hình và biển báo đến khu vực <strong>{location || 'khoa khám'}</strong>.
      </p>
    </div>
  )
}
