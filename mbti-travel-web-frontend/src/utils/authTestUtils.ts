import { AuthService } from '@/services/authService'
import type { AuthToken, UserContext } from '@/types/api'

/**
 * Utility functions for testing authentication functionality
 */
export class AuthTestUtils {
    /**
     * Create a mock JWT token for testing
     */
    static createMockJWT(payload: Partial<{
        sub: string
        email: string
        name: string
        exp: number
        iat: number
    }> = {}): string {
        const header = {
            alg: 'HS256',
            typ: 'JWT'
        }

        const defaultPayload = {
            sub: 'test-user-123',
            email: 'test@example.com',
            name: 'Test User',
            exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
            iat: Math.floor(Date.now() / 1000)
        }

        const finalPayload = { ...defaultPayload, ...payload }

        // Base64 encode header and payload
        const encodedHeader = btoa(JSON.stringify(header))
        const encodedPayload = btoa(JSON.stringify(finalPayload))

        // Create a mock signature (not cryptographically valid)
        const signature = btoa('mock-signature')

        return `${encodedHeader}.${encodedPayload}.${signature}`
    }

    /**
     * Create a mock expired JWT token
     */
    static createExpiredMockJWT(): string {
        return this.createMockJWT({
            exp: Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
        })
    }

    /**
     * Create mock auth token
     */
    static createMockAuthToken(overrides: Partial<AuthToken> = {}): AuthToken {
        return {
            accessToken: this.createMockJWT(),
            refreshToken: 'mock-refresh-token',
            expiresAt: Date.now() + 3600000, // 1 hour from now
            tokenType: 'Bearer',
            ...overrides
        }
    }

    /**
     * Create mock user context
     */
    static createMockUserContext(overrides: Partial<UserContext> = {}): UserContext {
        return {
            id: 'test-user-123',
            email: 'test@example.com',
            name: 'Test User',
            lastLogin: new Date().toISOString(),
            ...overrides
        }
    }

    /**
     * Test authentication service functionality
     */
    static async testAuthService(): Promise<void> {
        console.log('🧪 Testing AuthService...')

        const authService = AuthService.getInstance()

        // Test 1: Valid token validation
        const validToken = this.createMockJWT()
        const isValid = await authService.validateToken(validToken)
        console.log(`✅ Valid token validation: ${isValid ? 'PASS' : 'FAIL'}`)

        // Test 2: Expired token validation
        const expiredToken = this.createExpiredMockJWT()
        const isExpiredValid = await authService.validateToken(expiredToken)
        console.log(`✅ Expired token validation: ${!isExpiredValid ? 'PASS' : 'FAIL'}`)

        // Test 3: Invalid token validation
        const invalidToken = 'invalid.token.format'
        const isInvalidValid = await authService.validateToken(invalidToken)
        console.log(`✅ Invalid token validation: ${!isInvalidValid ? 'PASS' : 'FAIL'}`)

        // Test 4: Authentication state
        const initialAuth = authService.isAuthenticated()
        console.log(`✅ Initial auth state: ${!initialAuth ? 'PASS' : 'FAIL'}`)

        // Test 5: Set token and check authentication
        const mockToken = this.createMockAuthToken()
        const mockUser = this.createMockUserContext()
        authService.setToken(mockToken, mockUser)

        const afterSetAuth = authService.isAuthenticated()
        console.log(`✅ Auth after setToken: ${afterSetAuth ? 'PASS' : 'FAIL'}`)

        const currentUser = authService.getCurrentUser()
        console.log(`✅ Current user retrieval: ${currentUser?.id === mockUser.id ? 'PASS' : 'FAIL'}`)

        // Test 6: Logout
        authService.logout()
        const afterLogoutAuth = authService.isAuthenticated()
        console.log(`✅ Auth after logout: ${!afterLogoutAuth ? 'PASS' : 'FAIL'}`)

        console.log('🎉 AuthService tests completed!')
    }

    /**
     * Clear all authentication data (useful for testing)
     */
    static clearAuthData(): void {
        const authService = AuthService.getInstance()
        authService.logout()

        // Clear any remaining data
        localStorage.clear()
        document.cookie.split(";").forEach((c) => {
            const eqPos = c.indexOf("=")
            const name = eqPos > -1 ? c.substr(0, eqPos) : c
            document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/"
        })
    }
}

// Export for console testing
if (typeof window !== 'undefined') {
    (window as any).AuthTestUtils = AuthTestUtils
}