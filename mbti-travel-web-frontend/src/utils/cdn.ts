/**
 * CDN Utilities
 * Helper functions for CDN asset management
 */

import { config } from '@/config/environment';

/**
 * Get CDN URL for an asset
 */
export function getCdnUrl(assetPath: string): string {
  if (!config.cdnUrl) {
    return assetPath;
  }
  
  // Remove leading slash from asset path
  const cleanPath = assetPath.startsWith('/') ? assetPath.slice(1) : assetPath;
  
  // Ensure CDN URL doesn't end with slash
  const cleanCdnUrl = config.cdnUrl.endsWith('/') 
    ? config.cdnUrl.slice(0, -1) 
    : config.cdnUrl;
  
  return `${cleanCdnUrl}/${cleanPath}`;
}

/**
 * Get optimized image URL with CDN transformations
 */
export function getOptimizedImageUrl(
  imagePath: string, 
  options: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'avif' | 'jpg' | 'png';
  } = {}
): string {
  const baseUrl = getCdnUrl(imagePath);
  
  // If no CDN is configured, return original path
  if (!config.cdnUrl) {
    return baseUrl;
  }
  
  // Build query parameters for image optimization
  const params = new URLSearchParams();
  
  if (options.width) {
    params.append('w', options.width.toString());
  }
  
  if (options.height) {
    params.append('h', options.height.toString());
  }
  
  if (options.quality) {
    params.append('q', options.quality.toString());
  }
  
  if (options.format) {
    params.append('f', options.format);
  }
  
  const queryString = params.toString();
  return queryString ? `${baseUrl}?${queryString}` : baseUrl;
}

/**
 * Preload critical assets
 */
export function preloadCriticalAssets(): void {
  const criticalAssets = [
    // Preload critical CSS (main.css is bundled by Vite, no need to preload)
    // '/assets/styles/main.css',
    // Preload critical fonts
    '/assets/fonts/inter-regular.woff2',
    '/assets/fonts/inter-medium.woff2',
  ];
  
  criticalAssets.forEach(asset => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = getCdnUrl(asset);
    
    if (asset.endsWith('.css')) {
      link.as = 'style';
    } else if (asset.endsWith('.woff2') || asset.endsWith('.woff')) {
      link.as = 'font';
      link.type = 'font/woff2';
      link.crossOrigin = 'anonymous';
    }
    
    document.head.appendChild(link);
  });
}

/**
 * Generate responsive image srcset
 */
export function generateResponsiveImageSrcSet(
  imagePath: string,
  sizes: number[] = [320, 640, 768, 1024, 1280, 1920]
): string {
  return sizes
    .map(size => `${getOptimizedImageUrl(imagePath, { width: size, format: 'webp' })} ${size}w`)
    .join(', ');
}

/**
 * Check if CDN is available
 */
export async function checkCdnAvailability(): Promise<boolean> {
  if (!config.cdnUrl) {
    return false;
  }
  
  try {
    const response = await fetch(`${config.cdnUrl}/health`, {
      method: 'HEAD',
      mode: 'no-cors'
    });
    return response.ok;
  } catch {
    return false;
  }
}