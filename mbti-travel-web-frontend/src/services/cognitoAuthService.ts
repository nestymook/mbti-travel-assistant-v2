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
      await signOut()
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
      return null
    }

    try {
      const user = await getCurrentUser()
      const session = await fetchAuthSession()

      if (session.tokens) {
        return {
          id: user.userId,
          email: user.signInDetails?.loginId || 'unknown',
          name: user.signInDetails?.loginId?.split('@')[0] || 'User',
          roles: ['user'],
          preferences: {
            theme: 'light',
            language: 'en'
          }
        }
      }

      return null
    } catch (error) {
      console.error('Failed to get current user:', error)
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
      await signOut()
    } catch (error) {
      console.error('Hosted UI sign out failed:', error)
      // Don't throw error for logout failures, just redirect
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
}

// Export singleton instance
export const cognitoAuth = CognitoAuthService.getInstance()