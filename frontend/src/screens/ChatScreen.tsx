import { useState } from 'react'
import { VoiceButton } from '../components/VoiceButton'
import { BigButton, Spinner, StatusBar } from '../components/ui'
import { useKiosk } from '../hooks/useKiosk'

type Kiosk = ReturnType<typeof useKiosk>

/** 06. Hội thoại AI — voice-first, transcript, fallback text/touch. */
export function ChatScreen({ kiosk }: { kiosk: Kiosk }) {
  const [text, setText] = useState('')

  const send = () => {
    const t = text.trim()
    if (!t) return
    setText('')
    void kiosk.sendText(t)
  }

  return (
    <div className="screen chat">
      <div className="chat-head">
        <div className="avatar">🤖</div>
        <StatusBar>{kiosk.busy ? <Spinner label="Đang xử lý..." /> : '🟢 Sẵn sàng — nói hoặc gõ'}</StatusBar>
      </div>

      <div className="chat-messages" aria-live="polite">
        {kiosk.messages.map((m, i) => (
          <div key={i} className={`msg msg-${m.role}`}>{m.text}</div>
        ))}
        {kiosk.error && <div className="msg msg-emergency">⚠️ {kiosk.error}</div>}
      </div>

      <div className="chat-input-row">
        <VoiceButton onAudio={(blob) => kiosk.sendVoice(blob)} disabled={kiosk.busy} />
        <input
          className="big-input"
          placeholder="Nhập câu trả lời..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
        />
        <BigButton onClick={send} disabled={!text.trim() || kiosk.busy}>Gửi</BigButton>
      </div>

      <div className="exit-row">
        <BigButton variant="secondary" onClick={kiosk.reset}>↩️ Quay lại</BigButton>
        <BigButton variant="danger" onClick={kiosk.reset}>🆘 Gọi nhân viên</BigButton>
      </div>
    </div>
  )
}
