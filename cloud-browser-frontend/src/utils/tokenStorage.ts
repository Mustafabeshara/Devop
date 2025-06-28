import { AuthTokens } from '../types/auth'

const TOKEN_STORAGE_KEY = 'cloud_browser_tokens'

export function getStoredTokens(): AuthTokens | null {
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!stored) return null
    
    const tokens = JSON.parse(stored) as AuthTokens
    
    // Validate token structure
    if (!tokens.access_token || !tokens.refresh_token) {
      removeStoredTokens()
      return null
    }
    
    return tokens
  } catch (error) {
    console.error('Error retrieving stored tokens:', error)
    removeStoredTokens()
    return null
  }
}

export function setStoredTokens(tokens: AuthTokens): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens))
  } catch (error) {
    console.error('Error storing tokens:', error)
  }
}

export function removeStoredTokens(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch (error) {
    console.error('Error removing stored tokens:', error)
  }
}

export function getAccessToken(): string | null {
  const tokens = getStoredTokens()
  return tokens?.access_token || null
}

export function isTokenExpired(tokens: AuthTokens): boolean {
  try {
    const token = tokens.access_token
    const payload = JSON.parse(atob(token.split('.')[1]))
    const currentTime = Math.floor(Date.now() / 1000)
    
    return payload.exp < currentTime
  } catch (error) {
    console.error('Error checking token expiration:', error)
    return true
  }
}

export function getTokenExpiryTime(tokens: AuthTokens): Date | null {
  try {
    const token = tokens.access_token
    const payload = JSON.parse(atob(token.split('.')[1]))
    
    return new Date(payload.exp * 1000)
  } catch (error) {
    console.error('Error getting token expiry time:', error)
    return null
  }
}

export function clearAllStoredData(): void {
  try {
    // Clear tokens
    removeStoredTokens()
    
    // Clear any other app-specific data
    const keysToRemove = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith('cloud_browser_')) {
        keysToRemove.push(key)
      }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key))
  } catch (error) {
    console.error('Error clearing stored data:', error)
  }
}
