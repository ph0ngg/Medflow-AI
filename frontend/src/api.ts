// API client — MedFlow AI frontend

const BASE = '/api/kiosk'

async function json(res: Response): Promise<any> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
  }
  return res.json()
}

export async function detectFace(image: Blob) {
  const fd = new FormData()
  fd.append('image', image, 'frame.jpg')
  return json(await fetch(`${BASE}/detect-face`, { method: 'POST', body: fd }))
}

export async function startSession(faceName?: string | null, faceId?: string | null) {
  const fd = new FormData()
  if (faceName) fd.append('face_name', faceName)
  if (faceId) fd.append('face_id', faceId)
  return json(await fetch(`${BASE}/start-session`, { method: 'POST', body: fd }))
}

export async function register(fields: {
  full_name: string; dob: string; address: string; phone: string; cccd?: string; bhyt_code?: string
}, faceImage?: Blob | null) {
  const fd = new FormData()
  fd.append('full_name', fields.full_name)
  fd.append('dob', fields.dob)
  fd.append('address', fields.address)
  fd.append('phone', fields.phone)
  if (fields.cccd) fd.append('cccd', fields.cccd)
  if (fields.bhyt_code) fd.append('bhyt_code', fields.bhyt_code)
  if (faceImage) fd.append('face_image', faceImage, 'face.jpg')
  return json(await fetch(`${BASE}/register`, { method: 'POST', body: fd }))
}

export async function scanCccd(image: Blob) {
  const fd = new FormData()
  fd.append('image', image, 'cccd.jpg')
  return json(await fetch(`${BASE}/scan-cccd`, { method: 'POST', body: fd }))
}

export async function verifyCccd(sessionId: string, cccd?: string, code?: string) {
  const fd = new FormData()
  fd.append('session_id', sessionId)
  if (cccd) fd.append('cccd', cccd)
  if (code) fd.append('code', code)
  return json(await fetch(`${BASE}/verify-cccd`, { method: 'POST', body: fd }))
}

export async function sendMessage(sessionId: string, message: string) {
  return json(await fetch(`${BASE}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  }))
}

export async function sendVoice(sessionId: string, audio: Blob) {
  const fd = new FormData()
  fd.append('session_id', sessionId)
  fd.append('audio', audio, 'voice.webm')
  return json(await fetch(`${BASE}/voice-message`, { method: 'POST', body: fd }))
}

export async function selectDepartment(sessionId: string, department: string) {
  const fd = new FormData()
  fd.append('session_id', sessionId)
  fd.append('department', department)
  return json(await fetch(`${BASE}/select-department`, { method: 'POST', body: fd }))
}

export async function pay(sessionId: string, method = 'mock') {
  const fd = new FormData()
  fd.append('session_id', sessionId)
  fd.append('method', method)
  return json(await fetch(`${BASE}/pay`, { method: 'POST', body: fd }))
}

export async function confirm(sessionId: string) {
  return json(await fetch(`${BASE}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  }))
}

export async function endSession(sessionId: string) {
  return json(await fetch(`${BASE}/end-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  }))
}

export async function getDepartments() {
  return json(await fetch(`${BASE}/departments`))
}

export async function getQueue(department: string) {
  return json(await fetch(`${BASE}/queue/${encodeURIComponent(department)}`))
}

export async function tts(text: string): Promise<HTMLAudioElement> {
  const res = await fetch(`${BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: '', message: text }),
  })
  const blob = await res.blob()
  return new Audio(URL.createObjectURL(blob))
}
