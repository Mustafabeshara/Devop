import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, AuthTokens } from '../types/auth'
import { authApi } from '../services/api'
import { getStoredTokens, setStoredTokens, removeStoredTokens } from '../utils/tokenStorage'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  tokens: AuthTokens | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
}

interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [tokens, setTokens] = useState<AuthTokens | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!tokens

  // Initialize auth state from stored tokens
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = getStoredTokens()
        if (storedTokens) {
          setTokens(storedTokens)
          
          // Validate token and get user info
          const response = await authApi.validateToken()
          setUser(response.data.user)
        }
      } catch (error) {
        console.error('Token validation failed:', error)
        removeStoredTokens()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Set up token refresh timer
  useEffect(() => {
    if (!tokens) return

    const tokenRefreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Token refresh failed:', error)
        logout()
      }
    }, 50 * 60 * 1000) // Refresh every 50 minutes

    return () => clearInterval(tokenRefreshInterval)
  }, [tokens])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await authApi.login({ email, password })
      
      const authData = response.data
      const newTokens: AuthTokens = {
        access_token: authData.access_token,
        refresh_token: authData.refresh_token,
        expires_in: authData.expires_in
      }
      
      setTokens(newTokens)
      setUser(authData.user)
      setStoredTokens(newTokens)
      
      toast.success('Login successful!')
    } catch (error: any) {
      const message = error.response?.data?.error?.message || 'Login failed'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      setIsLoading(true)
      const response = await authApi.register(userData)
      
      const authData = response.data
      const newTokens: AuthTokens = {
        access_token: authData.access_token,
        refresh_token: authData.refresh_token,
        expires_in: authData.expires_in
      }
      
      setTokens(newTokens)
      setUser(authData.user)
      setStoredTokens(newTokens)
      
      toast.success('Registration successful!')
    } catch (error: any) {
      const message = error.response?.data?.error?.message || 'Registration failed'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      if (tokens) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      setUser(null)
      setTokens(null)
      removeStoredTokens()
      toast.success('Logged out successfully')
    }
  }

  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      const newTokens: AuthTokens = {
        access_token: response.data.access_token,
        refresh_token: tokens?.refresh_token || '',
        expires_in: response.data.expires_in
      }
      
      setTokens(newTokens)
      setStoredTokens(newTokens)
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      throw error
    }
  }

  const updateProfile = async (data: Partial<User>) => {
    try {
      const response = await authApi.updateProfile(data)
      if (response.data.data?.user) {
        setUser(response.data.data.user)
      }
      toast.success('Profile updated successfully')
    } catch (error: any) {
      const message = error.response?.data?.error?.message || 'Profile update failed'
      toast.error(message)
      throw error
    }
  }

  const contextValue: AuthContextType = {
    user,
    tokens,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}
