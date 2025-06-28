export interface BrowserSession {
  id: string
  user_id: number
  session_name: string
  browser_type: BrowserType
  status: SessionStatus
  container_id?: string
  container_name?: string
  docker_image?: string
  vnc_port?: number
  web_port?: number
  access_url?: string
  cpu_limit: number
  memory_limit: string
  storage_limit: string
  created_at: string
  started_at?: string
  last_accessed?: string
  expires_at?: string
  stopped_at?: string
  initial_url?: string
  screen_resolution: string
  page_views: number
  data_transferred: number
  session_duration: number
  is_active: boolean
  is_expired: boolean
  time_remaining?: number
  uptime: number
  error_message?: string
  error_count: number
  settings?: Record<string, any>
  container_status?: ContainerStatus
}

export type BrowserType = 'firefox' | 'chrome' | 'chromium'

export type SessionStatus = 
  | 'creating'
  | 'running' 
  | 'stopping'
  | 'stopped'
  | 'error'
  | 'expired'

export interface ContainerStatus {
  status: string
  created?: string
  started_at?: string
  cpu_usage_percent: number
  memory_usage_bytes: number
  memory_limit_bytes: number
  memory_usage_percent: number
  network_rx_bytes: number
  network_tx_bytes: number
  is_running: boolean
  error?: string
}

export interface CreateSessionRequest {
  browser_type: BrowserType
  session_name?: string
  initial_url?: string
  screen_resolution?: string
}

export interface SessionConnectionInfo {
  access_url: string
  vnc_port: number
  web_port: number
  time_remaining?: number
}

export interface SessionsResponse {
  sessions: BrowserSession[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
    has_prev: boolean
    has_next: boolean
  }
}

export interface SessionMetrics {
  total_sessions: number
  active_sessions: number
  total_session_time_seconds: number
  total_session_time_hours: number
  most_used_browser?: string
  browser_usage: Record<string, number>
}
