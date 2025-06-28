// Generic API response structure
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  timestamp: string
  meta?: Record<string, any>
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: any
  }
  timestamp: string
  meta?: Record<string, any>
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
    has_prev: boolean
    has_next: boolean
  }
}

// Health check responses
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  version: string
  components?: Record<string, ComponentHealth>
}

export interface ComponentHealth {
  status: 'healthy' | 'unhealthy' | 'degraded'
  message: string
  info?: Record<string, any>
}

export interface SystemMetrics {
  timestamp: string
  users: {
    total: number
    active: number
  }
  sessions: {
    total: number
    running: number
    creating: number
    stopped: number
  }
  docker?: {
    containers_running: number
    containers_total: number
    images_count: number
  }
}

// Admin types
export interface AdminStats {
  users: {
    total: number
    active: number
    new_last_24h: number
  }
  sessions: {
    total: number
    active: number
    new_last_24h: number
  }
  browser_usage: Record<string, number>
  docker_resources: DockerResources
  recent_events: AuditLogEntry[]
}

export interface DockerResources {
  docker_version: string
  containers_running: number
  containers_total: number
  images_count: number
  memory_total: number
  cpu_count: number
  storage_driver: string
  kernel_version: string
  operating_system: string
  server_version: string
}

export interface AuditLogEntry {
  id: number
  event_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  message?: string
  description?: string
  user_id?: number
  session_id?: string
  username?: string
  ip_address?: string
  user_agent?: string
  request_method?: string
  request_url?: string
  response_status?: number
  response_time_ms?: number
  resource_type?: string
  resource_id?: string
  old_values?: Record<string, any>
  new_values?: Record<string, any>
  metadata?: Record<string, any>
  tags?: string[]
  timestamp: string
  user?: {
    id: number
    username: string
    email: string
  }
}

export interface CleanupResults {
  expired_containers?: number
  expired_sessions?: number
  old_audit_logs?: number
}

// Error types for different HTTP status codes
export interface ValidationErrors {
  [field: string]: string[]
}

export interface RateLimitError {
  retry_after?: number
  limit?: string
}

// Request/Response interceptor types
export interface RequestConfig {
  url?: string
  method?: string
  headers?: Record<string, string>
  params?: Record<string, any>
  data?: any
  timeout?: number
}

export interface ResponseConfig {
  status: number
  statusText: string
  headers: Record<string, string>
  data: any
}

// File upload types
export interface FileUploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface UploadedFile {
  name: string
  size: number
  type: string
  url: string
  id?: string
}
