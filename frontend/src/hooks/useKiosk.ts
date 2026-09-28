import { useCallback, useState } from 'react'
import * as api from '../api'
import type {
  ChatMessage, Department, KioskResponse, Payment, Profile,
  QueueInfo, SessionState, Ticket,
} from '../types'

export type ScreenKey =
  | 'home' | 'faceLogin' | 'auth' | 'register' | 'menu'
  | 'profile' | 'chat' | 'department' | 'departments'
  | 'payment' | 'confirm' | 'ticket' | 'emergency' | 'end'

function screenFor(state: SessionState | undefined, ticket?: Ticket): ScreenKey {
  switch (state) {
    case 'identifying':
    case 'auth_cccd':
      return 'auth'
    case 'profile_review':
      return 'profile'
    case 'greeting':
    case 'collecting':
      return 'chat'
    case 'triaging':
    case 'queue_review':
      return 'department'
    case 'payment':
      return 'payment'
    case 'confirming':
      return 'confirm'
    case 'issuing':
    case 'done':
      return ticket ? 'ticket' : 'end'
    case 'emergency':
      return 'emergency'
    default:
      return 'home'
  }
}

export function useKiosk() {
  const [screen, setScreen] = useState<ScreenKey>('home')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [state, setState] = useState<SessionState>('idle')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [profile, setProfile] = useState<Profile | null>(null)
  const [patientName, setPatientName] = useState<string | null>(null)
  const [isReturning, setIsReturning] = useState(false)
  const [suggestedDept, setSuggestedDept] = useState<string | null>(null)
  const [deptReason, setDeptReason] = useState<string | null>(null)
  const [queueInfo, setQueueInfo] = useState<QueueInfo | null>(null)
  const [payment, setPayment] = useState<Payment | null>(null)
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [departments, setDepartments] = useState<Department[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pushAssistant = useCallback((text?: string) => {
    if (text) setMessages((m) => [...m, { role: 'assistant', text }])
  }, [])

  const pushUser = useCallback((text: string) => {
    setMessages((m) => [...m, { role: 'user', text }])
  }, [])

  const apply = useCallback((res: KioskResponse) => {
    if (res.session_id) setSessionId(res.session_id)
    if (res.state) setState(res.state)
    if (res.profile) setProfile(res.profile)
    if (res.patient_name) setPatientName(res.patient_name)
    if (typeof res.is_returning === 'boolean') setIsReturning(res.is_returning)
    if (res.suggested_department) setSuggestedDept(res.suggested_department)
    if (res.dept_reason) setDeptReason(res.dept_reason)
    if (res.queue_info) setQueueInfo(res.queue_info)
    if (res.payment) setPayment(res.payment)
    if (res.ticket) setTicket(res.ticket)
    if (res.departments) setDepartments(res.departments)
    if (res.response) pushAssistant(res.response)
    else if (res.greeting) pushAssistant(res.greeting)
    else if (res.message) pushAssistant(res.message)
    setScreen(screenFor(res.state, res.ticket))
  }, [pushAssistant])

  const run = useCallback(async (fn: () => Promise<KioskResponse>) => {
    setBusy(true)
    setError(null)
    try {
      const res = await fn()
      apply(res)
      return res
    } catch (e: any) {
      const msg = e?.message || 'Lỗi kết nối backend'
      setError(msg)
      pushAssistant(`⚠️ ${msg}`)
      return null
    } finally {
      setBusy(false)
    }
  }, [apply, pushAssistant])

  // ── Actions ─────────────────────────────────────────
  const goHome = useCallback(() => setScreen('home'), [])
  const goToMenu = useCallback(() => setScreen('menu'), [])
  const goToChat = useCallback(() => setScreen('chat'), [])
  const goToFaceLogin = useCallback(() => setScreen('faceLogin'), [])
  const goToRegister = useCallback(() => setScreen('register'), [])

  // Đăng nhập bằng khuôn mặt → thành công vào menu chọn khoa/chatbot
  const startWithFace = useCallback(async (name?: string | null, id?: string | null) => {
    setMessages([])
    const res = await run(() => api.startSession(name, id))
    if (res && !res.error) setScreen('menu')
    return res
  }, [run, setMessages])

  const startNew = useCallback(() => run(() => api.startSession(null, null)), [run])

  // Đăng nhập bằng CCCD/mã BN: tạo phiên rồi vào màn nhập CCCD
  const goToAuth = useCallback(async () => {
    if (!sessionId) await run(() => api.startSession(null, null))
    setScreen('auth')
  }, [sessionId, run])

  const verifyCccd = useCallback(async (cccd?: string, code?: string) => {
    if (!sessionId) return null
    setMessages([])
    const res = await run(() => api.verifyCccd(sessionId, cccd, code))
    if (res && !res.error) setScreen('menu')
    return res
  }, [run, sessionId, setMessages])

  const registerPatient = useCallback(async (fields: {
    full_name: string; dob: string; address: string; phone: string; cccd?: string; bhyt_code?: string
  }, faceImage?: Blob | null) => {
    setMessages([])
    const res = await run(() => api.register(fields, faceImage))
    if (res && !res.error) setScreen('menu')
    return res
  }, [run, setMessages])

  const sendText = useCallback((text: string) => {
    if (!sessionId) return Promise.resolve(null)
    pushUser(text)
    return run(() => api.sendMessage(sessionId, text))
  }, [run, sessionId, pushUser])

  const sendVoice = useCallback((blob: Blob) => {
    if (!sessionId) return Promise.resolve(null)
    return run(async () => {
      const res = await api.sendVoice(sessionId, blob)
      if (res?.transcribed_text) pushUser(res.transcribed_text)
      return res
    })
  }, [run, sessionId, pushUser])

  const chooseDepartment = useCallback((dept: string) => {
    if (!sessionId) return Promise.resolve(null)
    return run(() => api.selectDepartment(sessionId, dept))
  }, [run, sessionId])

  const loadDepartments = useCallback(async () => {
    try {
      const res = await api.getDepartments()
      setDepartments(res as Department[])
    } catch (e: any) {
      setError(e?.message || 'Không tải được danh sách khoa')
    }
  }, [])

  const goToDepartments = useCallback(async () => {
    if (!sessionId) {
      await run(() => api.startSession(null, null))
    }
    await loadDepartments()
    setScreen('departments')
  }, [sessionId, run, loadDepartments])

  const doPay = useCallback(() => {
    if (!sessionId) return Promise.resolve(null)
    return run(() => api.pay(sessionId))
  }, [run, sessionId])

  const doConfirm = useCallback(() => {
    if (!sessionId) return Promise.resolve(null)
    return run(() => api.confirm(sessionId))
  }, [run, sessionId])

  const speak = useCallback(async (text?: string) => {
    if (!text) return
    try {
      const audio = await api.tts(text)
      await audio.play()
    } catch {
      /* TTS optional */
    }
  }, [])

  const reset = useCallback(() => {
    if (sessionId) api.endSession(sessionId).catch(() => {})
    setSessionId(null)
    setState('idle')
    setMessages([])
    setProfile(null)
    setPatientName(null)
    setIsReturning(false)
    setSuggestedDept(null)
    setDeptReason(null)
    setQueueInfo(null)
    setPayment(null)
    setTicket(null)
    setDepartments([])
    setError(null)
    setScreen('home')
  }, [sessionId])

  return {
    screen, sessionId, state, messages, profile, patientName, isReturning,
    suggestedDept, deptReason, queueInfo, payment, ticket, departments,
    busy, error,
    goHome, goToMenu, goToChat, goToFaceLogin, goToRegister, goToAuth,
    startWithFace, startNew, verifyCccd, registerPatient, sendText, sendVoice,
    chooseDepartment, loadDepartments, goToDepartments, doPay, doConfirm, speak, reset,
  }
}
