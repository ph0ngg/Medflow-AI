import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { detectFace } from '../api'
import type { Face } from '../types'

export interface CameraFeedHandle {
  capture: () => Promise<Blob | null>
}

interface Props {
  autoDetect?: boolean
  detectInterval?: number
  onDetect?: (faces: Face[]) => void
}

/** Camera feed + capture frame (ảnh) để gửi lên backend detect/scan. */
export const CameraFeed = forwardRef<CameraFeedHandle, Props>(function CameraFeed(
  { autoDetect = false, detectInterval = 1500, onDetect },
  ref,
) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [camError, setCamError] = useState<string | null>(null)

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }, [])

  useEffect(() => {
    let cancelled = false
    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
      .then((stream) => {
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch(() => setCamError('Không thể truy cập camera.'))
    return () => { cancelled = true; stop() }
  }, [stop])

  const capture = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return null
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')?.drawImage(video, 0, 0)
    return new Promise((resolve) => canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.8))
  }, [])

  useImperativeHandle(ref, () => ({ capture }), [capture])

  // Auto-detect loop
  useEffect(() => {
    if (!autoDetect) return
    let cancelled = false
    let timer: ReturnType<typeof setInterval>
    const tick = async () => {
      const blob = await capture()
      if (!blob || cancelled) return
      try {
        const res = await detectFace(blob)
        if (!cancelled && res?.detected && onDetect) onDetect(res.faces || [])
      } catch { /* ignore */ }
    }
    const id = setInterval(() => { void tick() }, detectInterval)
    return () => { cancelled = true; clearInterval(id) }
  }, [autoDetect, detectInterval, onDetect, capture])

  return (
    <div className="camera-wrap">
      <video ref={videoRef} autoPlay playsInline muted />
      {camError && <div className="camera-error">{camError}</div>}
    </div>
  )
})
