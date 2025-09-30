import type { AuthToken, UserContext } from '@/types/api'

// Cookie configuration for secure token storage
interface CookieOptions {
  secure: boolean
  httpOnly: boolean
  sameSite: 'strict' | 'lax' | 'none'
  maxAge: number
}

// JWT payload interface
interface JWTPayload {
  sub: string
  email?: string
  name?: string
  exp: number
  iat: number
  iss?: string
  aud?: string
}

// Authentication service for JWT token management
export class AuthService {
  private static instance: AuthService
  private token: string | null = null
  private user: UserContext | null = null
  private refreshTimer: number | null = null

  // Cookie names for token storage
  private readonly ACCESS_TOKEN_KEY = 'mbti_access_token'
  private readonly REFRESH_TOKEN_KEY = 'mbti_refresh_token'
  private readonly USER_DATA_KEY = 'mbti_user_data'

  private constructor() {
    this.initializeFromStorage()
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService()
    }
    return AuthService.instance
  }

  /**
   * Initialize authentication state from stored tokens
   */
  private initializeFromStorage(): void {
    try {
      const storedToken = this.getStoredToken()
      const storedUser = this.getStoredUser()

      if (storedToken && this.isTokenValid(storedToken)) {
        this.token = storedToken
        this.user = storedUser
        this.scheduleTokenRefresh(storedToken)
      } else {
        this.clearStoredAuth()
      }
    } catch (error) {
      console.error('Failed to initialize auth from storage:', error)
      this.clearStoredAuth()
    }
  }

  /**
   * Validate JWT token structure and expiration
   */
  async validateToken(token: string): Promise<boolean> {
    try {
      if (!token || typeof token !== 'string') {
        return false
      }

      // Basic JWT structure validation
      const parts = token.split('.')
      if (parts.length !== 3) {
        return false
      }

      // Decode and validate payload
      const payload = this.decodeJWTPayload(token)
      if (!payload) {
        return false
      }

      // Check expiration
      const now = Math.floor(Date.now() / 1000)
      if (payload.exp <= now) {
        return false
      }

      // Additional validation can be added here
      // e.g., signature verification, issuer validation, etc.
      return true
    } catch (error) {
      console.error('Token validation failed:', error)
      return false
    }
  }

  /**
   * Refresh the JWT token
   */
  async refreshToken(): Promise<string> {
    try {
      const refreshToken = this.getStoredRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      // Make API call to refresh endpoint
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      })

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`)
      }

      const data = await response.json()
      const newToken: AuthToken = data.token

      // Store new tokens
      this.setToken(newToken)
      this.scheduleTokenRefresh(newToken.accessToken)

      return newToken.accessToken
    } catch (error) {
      console.error('Token refresh failed:', error)
      this.logout()
      throw new Error('Token refresh failed')
    }
  }

  /**
   * Redirect to login page
   */
  redirectToLogin(): void {
    // Clear any existing auth data
    this.logout()
    
    // Get current path to redirect back after login
    const currentPath = window.location.pathname
    const returnUrl = currentPath !== '/login' ? currentPath : '/'
    
    // Redirect to login with return URL
    const loginUrl = `/login?returnUrl=${encodeURIComponent(returnUrl)}`
    window.location.href = loginUrl
  }

  /**
   * Get current user context
   */
  getCurrentUser(): UserContext | null {
    return this.user
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (!this.token) {
      return false
    }

    return this.isTokenValid(this.token)
  }

  /**
   * Set authentication token and user data
   */
  setToken(authToken: AuthToken, userData?: UserContext): void {
    this.token = authToken.accessToken
    
    if (userData) {
      this.user = userData
      this.storeUser(userData)
    }

    // Store tokens securely
    this.storeToken(authToken.accessToken)
    if (authToken.refreshToken) {
      this.storeRefreshToken(authToken.refreshToken)
    }

    // Schedule token refresh
    this.scheduleTokenRefresh(authToken.accessToken)
  }

  /**
   * Get current access token
   */
  getToken(): string | null {
    return this.token
  }

  /**
   * Logout user and clear all auth data
   */
  logout(): void {
    this.token = null
    this.user = null
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }

    this.clearStoredAuth()
  }

  /**
   * Login with credentials
   */
  async login(email: string, password: string): Promise<UserContext> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`)
      }

      const data = await response.json()
      const { user, token } = data

      this.setToken(token, user)
      return user
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  /**
   * Check if token is valid (not expired)
   */
  private isTokenValid(token: string): boolean {
    try {
      const payload = this.decodeJWTPayload(token)
      if (!payload) return false

      const now = Math.floor(Date.now() / 1000)
      return payload.exp > now
    } catch {
      return false
    }
  }

  /**
   * Decode JWT payload without verification
   */
  private decodeJWTPayload(token: string): JWTPayload | null {
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return null

      const payload = parts[1]
      if (!payload) return null

      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
      return JSON.parse(decoded) as JWTPayload
    } catch {
      return null
    }
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(token: string): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
    }

    const payload = this.decodeJWTPayload(token)
    if (!payload) return

    // Refresh token 5 minutes before expiration
    const refreshTime = (payload.exp * 1000) - Date.now() - (5 * 60 * 1000)
    
    if (refreshTime > 0) {
      this.refreshTimer = window.setTimeout(() => {
        this.refreshToken().catch(() => {
          // If refresh fails, redirect to login
          this.redirectToLogin()
        })
      }, refreshTime)
    }
  }

  /**
   * Store token in secure cookie
   */
  private storeToken(token: string): void {
    const options: CookieOptions = {
      secure: window.location.protocol === 'https:',
      httpOnly: false, // Client-side access needed
      sameSite: 'strict',
      maxAge: 24 * 60 * 60 // 24 hours
    }

    this.setCookie(this.ACCESS_TOKEN_KEY, token, options)
  }

  /**
   * Store refresh token in secure cookie
   */
  private storeRefreshToken(refreshToken: string): void {
    const options: CookieOptions = {
      secure: window.location.protocol === 'https:',
      httpOnly: false,
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 // 7 days
    }

    this.setCookie(this.REFRESH_TOKEN_KEY, refreshToken, options)
  }

  /**
   * Store user data in localStorage
   */
  private storeUser(user: UserContext): void {
    try {
      localStorage.setItem(this.USER_DATA_KEY, JSON.stringify(user))
    } catch (error) {
      console.error('Failed to store user data:', error)
    }
  }

  /**
   * Get stored token from cookie
   */
  private getStoredToken(): string | null {
    return this.getCookie(this.ACCESS_TOKEN_KEY)
  }

  /**
   * Get stored refresh token from cookie
   */
  private getStoredRefreshToken(): string | null {
    return this.getCookie(this.REFRESH_TOKEN_KEY)
  }

  /**
   * Get stored user data from localStorage
   */
  private getStoredUser(): UserContext | null {
    try {
      const userData = localStorage.getItem(this.USER_DATA_KEY)
      return userData ? JSON.parse(userData) : null
    } catch {
      return null
    }
  }

  /**
   * Clear all stored authentication data
   */
  private clearStoredAuth(): void {
    this.deleteCookie(this.ACCESS_TOKEN_KEY)
    this.deleteCookie(this.REFRESH_TOKEN_KEY)
    localStorage.removeItem(this.USER_DATA_KEY)
  }

  /**
   * Set cookie with options
   */
  private setCookie(name: string, value: string, options: CookieOptions): void {
    let cookieString = `${name}=${encodeURIComponent(value)}`
    
    if (options.maxAge) {
      cookieString += `; Max-Age=${options.maxAge}`
    }
    
    if (options.secure) {
      cookieString += '; Secure'
    }
    
    if (options.sameSite) {
      cookieString += `; SameSite=${options.sameSite}`
    }
    
    cookieString += '; Path=/'
    
    document.cookie = cookieString
  }

  /**
   * Get cookie value by name
   */
  private getCookie(name: string): string | null {
    const nameEQ = name + '='
    const cookies = document.cookie.split(';')
    
    for (let cookie of cookies) {
      cookie = cookie.trim()
      if (cookie.indexOf(nameEQ) === 0) {
        return decodeURIComponent(cookie.substring(nameEQ.length))
      }
    }
    
    return null
  }

  /**
   * Delete cookie by name
   */
  private deleteCookie(name: string): void {
    document.cookie = `${name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;`
  }
}
