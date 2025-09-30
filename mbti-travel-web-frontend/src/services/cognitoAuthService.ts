import { Amplify } from 'aws-amplify'
import { signIn, signOut, getCurrentUser, fetchAuthSession, signUp, confirmSignUp, resendSignUpCode, signInWithRedirect } from '@aws-amplify/auth'
import type { UserContext, AuthToken } from '@/types/api'

// Cognito configuration interface
interface CognitoConfig {
  userPoolId: string
  userPoolClientId: string
  region: string
  domain?: string
  redirectSignIn?: string
  redirectSignOut?: string
}

// Cognito authentication service
export class CognitoAuthService {
  private static instance: CognitoAuthService
  private isConfigured = false

  private constructor() {
    this.initializeAmplify()
  }

  public static getInstance(): CognitoAuthService {
    if (!CognitoAuthService.instance) {
      CognitoAuthService.instance = new CognitoAuthService()
    }
    return CognitoAuthService.instance
  }

  /**
   * Initialize AWS Amplify with Cognito configuration
   */
  private initializeAmplify(): void {
    try {
      const config = this.getCognitoConfig()
      
      console.log('Configuring Amplify with:', {
        userPoolId: config.userPoolId,
        clientId: config.userPoolClientId,
        domain: config.domain,
        redirectSignIn: config.redirectSignIn,
        redirectSignOut: config.redirectSignOut,
        region: config.region
      })
      
      Amplify.configure({
        Auth: {
          Cognito: {
            userPoolId: config.userPoolId,
            userPoolClientId: config.userPoolClientId,
            loginWith: {
              oauth: {
                domain: config.domain ? `${config.domain}.auth.${config.region}.amazoncognito.com` : undefined,
                scopes: ['email', 'openid', 'profile'],
                redirectSignIn: [config.redirectSignIn || window.location.origin],
                redirectSignOut: [config.redirectSignOut || window.location.origin],
                responseType: 'code'
              },
              email: true,
              username: false
            },
            signUpVerificationMethod: 'code',
            userAttributes: {
              email: {
                required: true
              }
            },
            allowGuestAccess: false,
            passwordFormat: {
              minLength: 8,
              requireLowercase: true,
              requireUppercase: true,
              requireNumbers: true,
              requireSpecialCharacters: true
            }
          }
        }
      })

      this.isConfigured = true
      console.log('AWS Amplify configured successfully')
    } catch (error) {
      console.error('Failed to configure AWS Amplify:', error)
      this.isConfigured = false
    }
  }

  /**
   * Get Cognito configuration from environment variables
   */
  private getCognitoConfig(): CognitoConfig {
    const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
    const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID
    const domain = import.meta.env.VITE_COGNITO_DOMAIN
    const redirectSignIn = import.meta.env.VITE_COGNITO_REDIRECT_SIGN_IN
    const redirectSignOut = import.meta.env.VITE_COGNITO_REDIRECT_SIGN_OUT

    if (!userPoolId || !userPoolClientId) {
      throw new Error('Cognito configuration missing. Please set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID')
    }

    return {
      userPoolId,
      userPoolClientId,
      region: userPoolId.split('_')[0], // Extract region from user pool ID
      domain,
      redirectSignIn,
      redirectSignOut
    }
  }

  /**
   * Sign in with email and password
   */
  async login(email: string, password: string): Promise<UserContext> {
    if (!this.isConfigured) {
      throw new Error('Cognito service not configured')
    }

    try {
      const signInResult = await signIn({
        username: email,
        password: password
      })

      if (signInResult.isSignedIn) {
        // Get user details
        const user = await getCurrentUser()
        const session = await fetchAuthSession()

        const userData: UserContext = {
          id: user.userId,
          email: user.signInDetails?.loginId || email,
          name: user.signInDetails?.loginId?.split('@')[0] || 'User',
          roles: ['user'],
          preferences: {
            theme: 'light',
            language: 'en'
          }
        }

        return userData
      } else {
        throw new Error('Sign in incomplete. Additional steps may be required.')
      }
    } catch (error: any) {
      console.error('Cognito login failed:', error)
      
      // Handle specific Cognito errors
      if (error.name === 'NotAuthorizedException') {
        throw new Error('Invalid email or password')
      } else if (error.name === 'UserNotConfirmedException') {
        throw new Error('Please verify your email address before signing in')
      } else if (error.name === 'PasswordResetRequiredException') {
        throw new Error('Password reset required. Please reset your password.')
      } else if (error.name === 'UserNotFoundException') {
        throw new Error('User not found. Please check your email address.')
      } else if (error.name === 'TooManyRequestsException') {
        throw new Error('Too many login attempts. Please try again later.')
      }
      
      // Log the actual error for debugging
      console.error('Cognito login error details:', {
        name: error.name,
        message: error.message,
        code: error.code,
        stack: error.stack
      })
      
      throw new Error(error.message || 'Login failed')
    }
  }

  /**
   * Sign up a new user
   */
  async signUp(email: string, password: string, name?: string): Promise<void> {
    if (!this.isConfigured) {
      throw new Error('Cognito service not configured')
    }

    try {
      const signUpResult = await signUp({
        username: email,
        password: password,
        options: {
          userAttributes: {
            email: email,
            name: name || email.split('@')[0]
          }
        }
      })

      if (!signUpResult.isSignUpComplete) {
        // User needs to confirm their email
        console.log('Sign up successful. Please check your email for verification code.')
      }
    } catch (error: any) {
      console.error('Cognito sign up failed:', error)
      
      if (error.name === 'UsernameExistsException') {
        throw new Error('An account with this email already exists')
      } else if (error.name === 'InvalidPasswordException') {
        throw new Error('Password does not meet requirements')
      } else if (error.name === 'InvalidParameterException') {
        throw new Error('Invalid email address')
      }
      
      throw new Error(error.message || 'Sign up failed')
    }
  }

  /**
   * Confirm sign up with verification code
   */
  async confirmSignUp(email: string, confirmationCode: string): Promise<void> {
    if (!this.isConfigured) {
      throw new Error('Cognito service not configured')
    }

    try {
      await confirmSignUp({
        username: email,
        confirmationCode: confirmationCode
      })
    } catch (error: any) {
      console.error('Cognito confirmation failed:', error)
      
      if (error.name === 'CodeMismatchException') {
        throw new Error('Invalid verification code')
      } else if (error.name === 'ExpiredCodeException') {
        throw new Error('Verification code has expired')
      }
      
      throw new Error(error.message || 'Email verification failed')
    }
  }

  /**
   * Resend confirmation code
   */
  async resendConfirmationCode(email: string): Promise<void> {
    if (!this.isConfigured) {
      throw new Error('Cognito service not configured')
    }

    try {
      await resendSignUpCode({
        username: email
      })
    } catch (error: any) {
      console.error('Resend confirmation code failed:', error)
      throw new Error(error.message || 'Failed to resend confirmation code')
    }
  }

  /**
   * Sign out current user
   */
  async logout(): Promise<void> {
    if (!this.isConfigured) {
      return
    }

    try {
      await signOut({ global: true }) // Global sign out to invalidate all tokens
    } catch (error) {
      console.error('Cognito logout failed:', error)
      // Don't throw error for logout failures
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<UserContext | null> {
    if (!this.isConfigured) {
      console.log('Cognito service not configured')
      return null
    }

    try {
      console.log('Checking for current user...')
      
      // First check if we have a valid session
      const session = await fetchAuthSession()
      console.log('Session tokens available:', !!session.tokens?.accessToken)
      
      if (!session.tokens?.accessToken) {
        console.log('No valid tokens found in session')
        return null
      }

      // Then get user details
      const user = await getCurrentUser()
      console.log('User found:', user.userId)

      const userData = {
        id: user.userId,
        email: user.signInDetails?.loginId || 'unknown',
        name: user.signInDetails?.loginId?.split('@')[0] || 'User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          language: 'en'
        }
      }
      
      console.log('User data created:', userData)
      return userData
    } catch (error) {
      console.error('Failed to get current user:', error)
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      })
      return null
    }
  }

  /**
   * Get current auth token
   */
  async getAuthToken(): Promise<string | null> {
    if (!this.isConfigured) {
      return null
    }

    try {
      const session = await fetchAuthSession()
      return session.tokens?.accessToken?.toString() || null
    } catch (error) {
      console.error('Failed to get auth token:', error)
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    if (!this.isConfigured) {
      return false
    }

    try {
      const session = await fetchAuthSession()
      return !!session.tokens?.accessToken
    } catch (error) {
      return false
    }
  }

  /**
   * Validate current session
   */
  async validateSession(): Promise<boolean> {
    try {
      const session = await fetchAuthSession()
      return !!session.tokens?.accessToken
    } catch (error) {
      return false
    }
  }

  /**
   * Get configuration status
   */
  isConfigurationValid(): boolean {
    return this.isConfigured
  }

  /**
   * Clear all authentication state and configuration
   */
  async clearAuthState(): Promise<void> {
    try {
      // Sign out if configured
      if (this.isConfigured) {
        await signOut({ global: true })
      }
    } catch (error) {
      console.warn('Failed to sign out during state clearing:', error)
    }
    
    // Note: We don't reset Amplify configuration as it's needed for future logins
    // The configuration itself should persist, only the auth state should be cleared
  }

  /**
   * Sign in with Cognito Hosted UI
   */
  async signInWithHostedUI(): Promise<void> {
    if (!this.isConfigured) {
      throw new Error('Cognito service not configured')
    }

    try {
      await signInWithRedirect({
        provider: 'Cognito'
      })
    } catch (error: any) {
      console.error('Hosted UI sign in failed:', error)
      throw new Error(error.message || 'Authentication failed')
    }
  }

  /**
   * Sign out with redirect to Cognito Hosted UI
   */
  async signOutWithHostedUI(): Promise<void> {
    if (!this.isConfigured) {
      return
    }

    try {
      // First clear the local session
      await signOut({ global: true }) // Global sign out to invalidate all tokens
      
      // Then redirect to Cognito Hosted UI logout
      const logoutUrl = this.getHostedUILogoutUrl()
      window.location.href = logoutUrl
    } catch (error) {
      console.error('Hosted UI sign out failed:', error)
      // Even if logout fails, redirect to Cognito logout URL
      try {
        const logoutUrl = this.getHostedUILogoutUrl()
        window.location.href = logoutUrl
      } catch (urlError) {
        console.error('Failed to get logout URL:', urlError)
        // Final fallback - redirect to home page
        window.location.href = '/'
      }
    }
  }

  /**
   * Get Cognito Hosted UI login URL
   */
  getHostedUILoginUrl(): string {
    const config = this.getCognitoConfig()
    if (!config.domain) {
      throw new Error('Cognito domain not configured')
    }

    const params = new URLSearchParams({
      client_id: config.userPoolClientId,
      response_type: 'code',
      scope: 'email openid profile',
      redirect_uri: config.redirectSignIn || window.location.origin
    })

    return `https://${config.domain}.auth.${config.region}.amazoncognito.com/login?${params.toString()}`
  }

  /**
   * Get Cognito Hosted UI logout URL
   */
  getHostedUILogoutUrl(): string {
    const config = this.getCognitoConfig()
    if (!config.domain) {
      throw new Error('Cognito domain not configured')
    }

    const params = new URLSearchParams({
      client_id: config.userPoolClientId,
      logout_uri: config.redirectSignOut || window.location.origin
    })

    return `https://${config.domain}.auth.${config.region}.amazoncognito.com/logout?${params.toString()}`
  }

  /**
   * Logout directly through Cognito Hosted UI
   */
  logoutWithHostedUI(): void {
    try {
      const logoutUrl = this.getHostedUILogoutUrl()
      console.log('Redirecting to Cognito logout:', logoutUrl)
      window.location.href = logoutUrl
    } catch (error) {
      console.error('Failed to logout with Hosted UI:', error)
      // Fallback to home page
      window.location.href = '/'
    }
  }

  /**
   * Process OAuth callback and return authentication status
   */
  async processOAuthCallback(): Promise<boolean> {
    if (!this.isConfigured) {
      console.error('Cognito service not configured')
      return false
    }

    try {
      console.log('Processing OAuth callback...')
      
      // Get the authorization code from URL
      const urlParams = new URLSearchParams(window.location.search)
      const authCode = urlParams.get('code')
      const state = urlParams.get('state')
      
      console.log('OAuth callback parameters:', { authCode: !!authCode, state })
      
      if (!authCode) {
        console.error('No authorization code found in callback')
        return false
      }

      // Try to let Amplify handle the callback first
      console.log('Waiting for Amplify to process OAuth callback...')
      
      // Wait longer for Amplify to process the OAuth callback
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Check multiple times if we now have a valid session
      for (let attempt = 1; attempt <= 5; attempt++) {
        console.log(`Checking authentication status - attempt ${attempt}/5`)
        
        try {
          const session = await fetchAuthSession({ forceRefresh: true })
          const isAuthenticated = !!session.tokens?.accessToken
          
          console.log(`Attempt ${attempt}: authenticated =`, isAuthenticated)
          
          if (isAuthenticated) {
            console.log('OAuth callback successful!')
            
            // Verify we can get user details
            try {
              const user = await getCurrentUser()
              console.log('User authenticated:', user.userId)
              return true
            } catch (userError) {
              console.error('Failed to get user details:', userError)
              // Continue to next attempt
            }
          }
        } catch (sessionError) {
          console.error(`Session check attempt ${attempt} failed:`, sessionError)
        }
        
        // Wait before next attempt
        if (attempt < 5) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }
      
      console.error('OAuth callback processing failed after all attempts')
      return false
      
    } catch (error) {
      console.error('OAuth callback processing failed:', error)
      return false
    }
  }

  /**
   * Manual token exchange for OAuth callback
   */
  async exchangeCodeForTokens(authCode: string): Promise<any> {
    const config = this.getCognitoConfig()
    
    const tokenEndpoint = `https://${config.domain}.auth.${config.region}.amazoncognito.com/oauth2/token`
    
    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: config.userPoolClientId,
      code: authCode,
      redirect_uri: config.redirectSignIn || window.location.origin
    })

    try {
      const response = await fetch(tokenEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params.toString()
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Token exchange failed:', response.status, errorText)
        throw new Error(`Token exchange failed: ${response.status}`)
      }

      const tokens = await response.json()
      console.log('Token exchange successful:', { 
        hasAccessToken: !!tokens.access_token,
        hasIdToken: !!tokens.id_token,
        hasRefreshToken: !!tokens.refresh_token
      })
      
      return tokens
    } catch (error) {
      console.error('Manual token exchange failed:', error)
      throw error
    }
  }
}

// Export singleton instance
export const cognitoAuth = CognitoAuthService.getInstance()