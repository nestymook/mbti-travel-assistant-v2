/**
 * Environment Configuration
 * Centralized configuration management for different environments
 */

export interface EnvironmentConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;
  
  // Authentication Configuration
  cognito: {
    userPoolId: string;
    clientId: string;
    domain: string;
  };
  
  // External Links
  mbtiTestUrl: string;
  
  // Development Configuration
  enableDevtools: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  enableMockApi: boolean;
  
  // Performance Configuration
  enablePerformanceMonitoring: boolean;
  debounceDelay: number;
  
  // CDN Configuration
  cdnUrl: string;
  
  // Base URL for routing
  baseUrl: string;
  
  // Build Information
  version: string;
  buildTime: string;
}

/**
 * Get environment configuration
 */
export function getEnvironmentConfig(): EnvironmentConfig {
  return {
    // API Configuration
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
    apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),
    
    // Authentication Configuration
    cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
      clientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
      domain: import.meta.env.VITE_COGNITO_DOMAIN || '',
    },
    
    // External Links
    mbtiTestUrl: import.meta.env.VITE_MBTI_TEST_URL || 'https://www.16personalities.com',
    
    // Development Configuration
    enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true',
    logLevel: (import.meta.env.VITE_LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') || 'info',
    enableMockApi: import.meta.env.VITE_ENABLE_MOCK_API === 'true',
    
    // Performance Configuration
    enablePerformanceMonitoring: import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true',
    debounceDelay: parseInt(import.meta.env.VITE_DEBOUNCE_DELAY || '300', 10),
    
    // CDN Configuration
    cdnUrl: import.meta.env.VITE_CDN_URL || '',
    
    // Base URL for routing
    baseUrl: import.meta.env.VITE_BASE_URL || '/',
    
    // Build Information
    version: (globalThis as any).__APP_VERSION__ || '1.0.0',
    buildTime: (globalThis as any).__BUILD_TIME__ || new Date().toISOString(),
  };
}

/**
 * Check if running in development mode
 */
export function isDevelopment(): boolean {
  return import.meta.env.DEV;
}

/**
 * Check if running in production mode
 */
export function isProduction(): boolean {
  return import.meta.env.PROD;
}

/**
 * Get current environment mode
 */
export function getEnvironmentMode(): string {
  return import.meta.env.MODE || 'development';
}

/**
 * Validate required environment variables
 */
export function validateEnvironmentConfig(): void {
  const config = getEnvironmentConfig();
  const errors: string[] = [];
  
  // Validate required API configuration
  if (!config.apiBaseUrl) {
    errors.push('VITE_API_BASE_URL is required');
  }
  
  // Validate authentication configuration in production
  if (isProduction()) {
    if (!config.cognito.userPoolId) {
      errors.push('VITE_COGNITO_USER_POOL_ID is required in production');
    }
    if (!config.cognito.clientId) {
      errors.push('VITE_COGNITO_CLIENT_ID is required in production');
    }
    if (!config.cognito.domain) {
      errors.push('VITE_COGNITO_DOMAIN is required in production');
    }
  }
  
  if (errors.length > 0) {
    throw new Error(`Environment configuration errors:\n${errors.join('\n')}`);
  }
}

// Export singleton instance
export const config = getEnvironmentConfig();