/**
 * Build Configuration
 * Advanced build settings and optimizations
 */

export interface BuildConfig {
  // Bundle optimization
  chunkSizeWarningLimit: number;
  assetsInlineLimit: number;
  
  // Code splitting strategy
  splitVendorChunks: boolean;
  splitPersonalityChunks: boolean;
  
  // Asset optimization
  optimizeImages: boolean;
  generateWebp: boolean;
  compressAssets: boolean;
  
  // Performance
  enableTreeShaking: boolean;
  enableMinification: boolean;
  generateSourceMaps: boolean;
  
  // CDN
  enableCdn: boolean;
  cdnDomains: string[];
  
  // Security
  enableCSP: boolean;
  enableSRI: boolean;
}

export const buildConfigs: Record<string, BuildConfig> = {
  development: {
    chunkSizeWarningLimit: 2000,
    assetsInlineLimit: 4096,
    splitVendorChunks: false,
    splitPersonalityChunks: false,
    optimizeImages: false,
    generateWebp: false,
    compressAssets: false,
    enableTreeShaking: false,
    enableMinification: false,
    generateSourceMaps: true,
    enableCdn: false,
    cdnDomains: [],
    enableCSP: false,
    enableSRI: false,
  },
  
  staging: {
    chunkSizeWarningLimit: 1000,
    assetsInlineLimit: 4096,
    splitVendorChunks: true,
    splitPersonalityChunks: true,
    optimizeImages: true,
    generateWebp: true,
    compressAssets: true,
    enableTreeShaking: true,
    enableMinification: true,
    generateSourceMaps: true,
    enableCdn: true,
    cdnDomains: ['cdn-staging.mbti-travel.example.com'],
    enableCSP: true,
    enableSRI: true,
  },
  
  production: {
    chunkSizeWarningLimit: 500,
    assetsInlineLimit: 4096,
    splitVendorChunks: true,
    splitPersonalityChunks: true,
    optimizeImages: true,
    generateWebp: true,
    compressAssets: true,
    enableTreeShaking: true,
    enableMinification: true,
    generateSourceMaps: false,
    enableCdn: true,
    cdnDomains: ['cdn.mbti-travel.example.com'],
    enableCSP: true,
    enableSRI: true,
  },
};

export function getBuildConfig(mode: string): BuildConfig {
  return buildConfigs[mode] || buildConfigs.development;
}