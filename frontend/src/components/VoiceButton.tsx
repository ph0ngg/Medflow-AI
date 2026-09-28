import { useRef, useState } from 'react'

interface Props {
  onAudio: (blob: Blob) => void
  disabled?: boolean
}

const MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/mp4',
]

function pickMime(): string {
  for (const m of MIME_TYPES) if (MediaRecorder.isTypeSupported(m)) return m
  return ''
}

/** Nút ghi âm push-to-talk: giữ để nói, nhả để gửi. */
export function VoiceButton({ onAudio, disabled }: Props) {
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const [recording, setRecording] = useState(false)
  const [mime, setMime] = useState('audio/webm')

  const start = async () => {
    if (disabled || recorderRef.current) return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = pickMime()
      setMime(mimeType || 'audio/webm')
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' })
        stream.getTracks().forEach((t) => t.stop())
        recorderRef.current = null
        setRecording(false)
        if (blob.size > 0) onAudio(blob)
      }
      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch {
      /* mic unavailable */
    }
  }

  const stop = () => {
    recorderRef.current?.stop()
  }

  return (
    <button
      className={`voice-btn ${recording ? 'recording' : ''}`}
      onMouseDown={start}
      onMouseUp={stop}
      onMouseLeave={stop}
      onTouchStart={(e) => { e.preventDefault(); void start() }}
      onTouchEnd={stop}
      disabled={disabled}
      title="Giữ để nói"
    >
      🎤
    </button>
  )
}
