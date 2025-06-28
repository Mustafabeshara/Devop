export interface User {
  id: number
  email: string
  username: string
  first_name?: string
  last_name?: string
  full_name: string
  avatar_url?: string
  timezone?: string
  active: boolean
  confirmed_at?: string
  last_login_at?: string
  login_count: number
  is_admin: boolean
  max_containers: number
  container_timeout: number
  preferred_browser: string
  created_at: string
  roles: string[]
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface TokenRefreshResponse {
  access_token: string
  expires_in: number
}

export interface ValidationResponse {
  user: User
  token_info: {
    issued_at: number
    expires_at: number
    roles: string[]
    is_admin: boolean
  }
}
