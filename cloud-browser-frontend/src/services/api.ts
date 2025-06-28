import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios'
import toast from 'react-hot-toast'
import { 
  ApiResponse, 
  ApiError, 
  PaginatedResponse,
  HealthStatus,
  SystemMetrics,
  AdminStats,
  AuditLogEntry,
  CleanupResults
} from '../types/api'
import { 
  User, 
 
  LoginCredentials, 
  RegisterData, 
  AuthResponse,
  TokenRefreshResponse,
  ValidationResponse
} from '../types/auth'
import { 
  BrowserSession, 
  CreateSessionRequest, 
  SessionsResponse, 
  SessionConnectionInfo 
} from '../types/sessions'
import {
  AnalysisResult,
  CodeAnalysisResult,
  DebugResult,
  FileAnalysisResult,
  AnalysisStatus,
  AnalysisSession,
  SupportedLanguages,
  CodeAnalysisRequest,
  RepositoryAnalysisRequest,
  FileAnalysisRequest,
  DebugRequest
} from '../types/analysis'
import { getAccessToken, removeStoredTokens } from '../utils/tokenStorage'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors globally
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError<ApiError>) => {
    // Handle different error types
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - token expired or invalid
          removeStoredTokens()
          window.location.href = '/login'
          break
          
        case 403:
          // Forbidden
          toast.error('Access denied. Insufficient permissions.')
          break
          
        case 404:
          // Not found
          toast.error('Resource not found.')
          break
          
        case 429:
          // Rate limited
          toast.error('Too many requests. Please try again later.')
          break
          
        case 500:
          // Server error
          toast.error('Server error. Please try again later.')
          break
          
        case 503:
          // Service unavailable
          toast.error('Service temporarily unavailable.')
          break
          
        default:
          // Other errors
          const message = data?.error?.message || 'An unexpected error occurred'
          toast.error(message)
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.')
    } else {
      // Other error
      toast.error('An unexpected error occurred.')
    }
    
    return Promise.reject(error)
  }
)

// Authentication API
export const authApi = {
  login: (credentials: LoginCredentials): Promise<AxiosResponse<AuthResponse>> =>
    api.post('/auth/login', credentials),
    
  register: (userData: RegisterData): Promise<AxiosResponse<AuthResponse>> =>
    api.post('/auth/register', userData),
    
  logout: (): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/auth/logout'),
    
  refreshToken: (): Promise<AxiosResponse<TokenRefreshResponse>> =>
    api.post('/auth/refresh'),
    
  validateToken: (): Promise<AxiosResponse<ValidationResponse>> =>
    api.get('/auth/validate'),
    
  getProfile: (): Promise<AxiosResponse<ApiResponse<{ user: User; statistics: any }>>> =>
    api.get('/auth/profile'),
    
  updateProfile: (data: Partial<User>): Promise<AxiosResponse<ApiResponse<{ user: User }>>> =>
    api.put('/auth/profile', data),
    
  changePassword: (data: { current_password: string; new_password: string }): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/auth/change-password', data),
    
  setup2FA: (): Promise<AxiosResponse<ApiResponse<{ qr_code: string; secret: string }>>> =>
    api.post('/auth/2fa/setup'),
    
  verify2FA: (token: string): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/auth/2fa/verify', { token }),
}

// Sessions API
export const sessionsApi = {
  getSessions: (params?: {
    status?: string
    browser_type?: string
    page?: number
    per_page?: number
  }): Promise<AxiosResponse<ApiResponse<SessionsResponse>>> =>
    api.get('/sessions', { params }),
    
  createSession: (data: CreateSessionRequest): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.post('/sessions', data),
    
  getSession: (sessionId: string): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.get(`/sessions/${sessionId}`),
    
  updateSession: (sessionId: string, data: Partial<BrowserSession>): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.put(`/sessions/${sessionId}`, data),
    
  extendSession: (sessionId: string, hours: number = 1): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.post(`/sessions/${sessionId}/extend`, { hours }),
    
  stopSession: (sessionId: string): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.post(`/sessions/${sessionId}/stop`),
    
  deleteSession: (sessionId: string): Promise<AxiosResponse<ApiResponse>> =>
    api.delete(`/sessions/${sessionId}`),
    
  accessSession: (sessionId: string): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession; connection_info: SessionConnectionInfo }>>> =>
    api.post(`/sessions/${sessionId}/access`),
    
  cleanupSessions: (): Promise<AxiosResponse<ApiResponse<{ cleaned_sessions: number }>>> =>
    api.post('/sessions/cleanup'),
}

// Code Analysis API (Kimi-Dev-72B)
export const analysisApi = {
  analyzeRepository: (data: RepositoryAnalysisRequest): Promise<AxiosResponse<ApiResponse<{ analysis: AnalysisResult; repository: any }>>> =>
    api.post('/kimi/analyze/repository', data),
    
  analyzeCode: (data: CodeAnalysisRequest): Promise<AxiosResponse<ApiResponse<{ analysis: CodeAnalysisResult }>>> =>
    api.post('/kimi/analyze/code', data),
    
  analyzeFile: (data: FileAnalysisRequest): Promise<AxiosResponse<ApiResponse<{ analysis: FileAnalysisResult }>>> =>
    api.post('/kimi/analyze/file', data),
    
  debugIssue: (data: DebugRequest): Promise<AxiosResponse<ApiResponse<{ debug: DebugResult }>>> =>
    api.post('/kimi/debug', data),
    
  getAnalysisStatus: (analysisId: string): Promise<AxiosResponse<ApiResponse<{ status: AnalysisStatus }>>> =>
    api.get(`/kimi/analysis/${analysisId}/status`),
    
  getAnalysisResults: (analysisId: string): Promise<AxiosResponse<ApiResponse<{ results: any }>>> =>
    api.get(`/kimi/analysis/${analysisId}/results`),
    
  getSupportedLanguages: (): Promise<AxiosResponse<ApiResponse<SupportedLanguages>>> =>
    api.get('/kimi/languages'),
    
  createAnalysisSession: (): Promise<AxiosResponse<ApiResponse<{ session: AnalysisSession }>>> =>
    api.post('/kimi/session'),
}

// Health API
export const healthApi = {
  getHealth: (): Promise<AxiosResponse<HealthStatus>> =>
    api.get('/health'),
    
  getDetailedHealth: (): Promise<AxiosResponse<HealthStatus>> =>
    api.get('/health/detailed'),
    
  getMetrics: (): Promise<AxiosResponse<ApiResponse<SystemMetrics>>> =>
    api.get('/health/metrics'),
}

// Admin API
export const adminApi = {
  getUsers: (params?: {
    page?: number
    per_page?: number
    search?: string
  }): Promise<AxiosResponse<ApiResponse<PaginatedResponse<User>>>> =>
    api.get('/admin/users', { params }),
    
  getUser: (userId: number): Promise<AxiosResponse<ApiResponse<{ user: User; statistics: any; sessions: BrowserSession[] }>>> =>
    api.get(`/admin/users/${userId}`),
    
  activateUser: (userId: number): Promise<AxiosResponse<ApiResponse<{ user: User }>>> =>
    api.post(`/admin/users/${userId}/activate`),
    
  deactivateUser: (userId: number): Promise<AxiosResponse<ApiResponse<{ user: User }>>> =>
    api.post(`/admin/users/${userId}/deactivate`),
    
  unlockUser: (userId: number): Promise<AxiosResponse<ApiResponse<{ user: User }>>> =>
    api.post(`/admin/users/${userId}/unlock`),
    
  getAllSessions: (params?: {
    page?: number
    per_page?: number
    status?: string
    user_id?: number
  }): Promise<AxiosResponse<ApiResponse<PaginatedResponse<BrowserSession & { user: { id: number; username: string; email: string } }>>>> =>
    api.get('/admin/sessions', { params }),
    
  stopAnySession: (sessionId: string): Promise<AxiosResponse<ApiResponse<{ session: BrowserSession }>>> =>
    api.post(`/admin/sessions/${sessionId}/stop`),
    
  getSystemStats: (): Promise<AxiosResponse<ApiResponse<AdminStats>>> =>
    api.get('/admin/system/stats'),
    
  performCleanup: (): Promise<AxiosResponse<ApiResponse<CleanupResults>>> =>
    api.post('/admin/system/cleanup'),
    
  getAuditLogs: (params?: {
    page?: number
    per_page?: number
    event_type?: string
    user_id?: number
    severity?: string
  }): Promise<AxiosResponse<ApiResponse<PaginatedResponse<AuditLogEntry>>>> =>
    api.get('/admin/audit-logs', { params }),
    
  pullDockerImages: (): Promise<AxiosResponse<ApiResponse<{ results: Record<string, boolean> }>>> =>
    api.post('/admin/docker/pull-images'),
}

// Export the configured axios instance for custom requests
export default api
