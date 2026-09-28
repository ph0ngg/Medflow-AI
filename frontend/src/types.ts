// Shared types — mirror backend session/state contracts

export type SessionState =
  | 'idle'
  | 'detecting'
  | 'identifying'
  | 'auth_cccd'
  | 'profile_review'
  | 'greeting'
  | 'collecting'
  | 'triaging'
  | 'queue_review'
  | 'payment'
  | 'confirming'
  | 'issuing'
  | 'emergency'
  | 'done'

export interface QueueInfo {
  department?: string
  current_queue?: number
  estimated_wait?: number
  now_serving?: number
}

export interface Payment {
  payment_id?: number
  amount?: number
  insurance_covered?: number
  patient_pay?: number
  method?: string
  status?: string
}

export interface Ticket {
  ticket_id?: number
  ticket_number?: number
  department?: string
  location?: string
  estimated_wait?: number
}

export interface Profile {
  full_name?: string
  dob?: string
  cccd?: string
  phone?: string
  address?: string
  bhyt_code?: string
  insurance_valid?: boolean
  insurance_status?: string
  upcoming_appointments?: Appointment[]
  last_department?: string | null
  history?: HistoryItem[]
}

export interface Appointment {
  id: number
  department: string
  appointment_date: string
  appointment_time?: string
  status: string
}

export interface HistoryItem {
  department: string
  visit_date: string
  doctor_name?: string
  notes?: string
}

export interface Face {
  id?: string | null
  name?: string | null
}

export interface Department {
  id: number
  name: string
  location?: string
  services?: string
  current_queue?: number
  estimated_wait?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'emergency'
  text: string
}

/** Backend trả về từ hầu hết các endpoint — nới lỏng theo từng state. */
export interface KioskResponse {
  session_id?: string
  state?: SessionState
  intent?: string
  response?: string
  message?: string
  greeting?: string
  action?: string
  error?: string
  transcribed_text?: string

  patient_name?: string
  is_returning?: boolean
  identity_method?: string

  profile?: Profile
  symptoms?: string[]
  suggested_department?: string
  dept_reason?: string
  dept_confidence?: number
  queue_info?: QueueInfo
  payment?: Payment
  ticket?: Ticket
  departments?: Department[]
  detected?: boolean
  faces?: Face[]
  info?: { full_name?: string; dob?: string; cccd?: string; address?: string }
}
