# Routing and Navigation System Implementation

This document describes the comprehensive routing and navigation system implemented for the MBTI Travel Web Frontend.

## Overview

The routing system provides:
- ✅ Vue Router 4 with authentication guards and route protection
- ✅ Route definitions for input page, itinerary page, and login page
- ✅ Navigation between pages with state preservation
- ✅ Browser history management and deep linking support
- ✅ Route-based code splitting for performance optimization

## Key Features

### 1. Enhanced Router Configuration

**File**: `src/router/index.ts`

- **Route-based code splitting**: All routes use lazy loading for better performance
- **MBTI parameter validation**: Automatic validation and normalization of MBTI personality types
- **Scroll behavior**: Smooth scrolling with position restoration
- **Meta configuration**: Rich metadata for each route including titles and auth requirements

```typescript
// Example route with validation
{
  path: '/itinerary/:mbti',
  name: 'itinerary',
  component: () => import('../views/ItineraryPage.vue'),
  beforeEnter: (to, from, next) => {
    const mbti = to.params.mbti as string
    const validMBTI = /^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$/i
    
    if (!validMBTI.test(mbti)) {
      next({ name: 'home', query: { error: 'invalid-mbti' } })
    } else {
      next()
    }
  }
}
```

### 2. Authentication Guards

- **Global navigation guard**: Protects routes based on authentication status
- **State preservation**: Maintains user state during navigation
- **Return URL handling**: Supports deep linking after authentication
- **Token validation**: Validates JWT tokens before allowing access

### 3. Navigation Composable

**File**: `src/composables/useNavigation.ts`

Provides a comprehensive API for navigation:

```typescript
const {
  navigateTo,        // Enhanced navigation with options
  goBack,           // Browser back with fallback
  goHome,           // Navigate to home
  goToItinerary,    // Navigate to itinerary with MBTI
  getCurrentState,  // Get current route state
  restoreState,     // Restore preserved state
  routeExists,      // Check if route exists
  getRouteUrl       // Generate route URLs
} = useNavigation()
```

### 4. Route Preloader

**File**: `src/utils/routePreloader.ts`

Performance optimization through intelligent preloading:

- **Hover preloading**: Preload routes when user hovers over links
- **Intersection preloading**: Preload when elements come into view
- **Predictive preloading**: Preload likely next routes based on user behavior
- **Memory management**: Automatic cleanup of old preloaded routes

### 5. State Preservation

The system preserves navigation state including:
- Scroll positions
- Form data
- Route parameters and queries
- Timestamps for cleanup

### 6. Error Handling

Comprehensive error handling for:
- Authentication failures
- Network errors during route loading
- Chunk loading failures (with automatic retry)
- Invalid route parameters

## Usage Examples

### Basic Navigation

```vue
<template>
  <div>
    <!-- Basic router link with preloading -->
    <RouterLink to="/" v-preload-route="'home'">Home</RouterLink>
    
    <!-- Programmatic navigation -->
    <button @click="goToItinerary('ENFP')">View ENFP Itinerary</button>
  </div>
</template>

<script setup lang="ts">
import { useNavigation } from '@/composables/useNavigation'

const { goToItinerary } = useNavigation()
</script>
```

### State Preservation

```vue
<script setup lang="ts">
import { useNavigation, useRouteGuard } from '@/composables/useNavigation'

const { getCurrentState, restoreState } = useNavigation()
const { confirmNavigation } = useRouteGuard()

// Preserve state when navigating away
onBeforeUnmount(() => {
  if (hasUnsavedChanges.value) {
    const state = getCurrentState()
    // State is automatically preserved
  }
})

// Restore state when component mounts
onMounted(() => {
  const preservedState = restoreState()
  if (preservedState?.formData) {
    // Restore form data
    formData.value = preservedState.formData
  }
})

// Confirm navigation if there are unsaved changes
const removeGuard = confirmNavigation('You have unsaved changes. Continue?')
</script>
```

### Route Preloading

```vue
<template>
  <div>
    <!-- Preload on hover -->
    <RouterLink to="/about" v-preload-route="'about'">About</RouterLink>
    
    <!-- Preload when visible -->
    <div v-preload-on-visible="'itinerary'">
      <RouterLink to="/itinerary/ENFP">View Itinerary</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoutePreloader } from '@/utils/routePreloader'

const { preloadLikelyRoutes } = useRoutePreloader()

// Preload likely next routes
onMounted(() => {
  setTimeout(preloadLikelyRoutes, 2000)
})
</script>
```

## Route Structure

```
/                     → InputPage (requires auth)
/login               → LoginView (hidden when authenticated)
/itinerary/:mbti     → ItineraryPage (requires auth, validates MBTI)
/about               → AboutView (public)
/*                   → NotFoundView (404 page)
```

## Authentication Flow

1. User accesses protected route
2. Authentication guard checks token validity
3. If invalid: redirect to login with return URL
4. If valid: allow access and restore any preserved state
5. After login: redirect to original destination

## Performance Optimizations

### Code Splitting
- All routes use dynamic imports
- Components are loaded only when needed
- Automatic chunk optimization by Vite

### Preloading Strategy
- Hover-based preloading for immediate navigation
- Intersection-based preloading for visible elements
- Predictive preloading based on user behavior patterns
- Memory management to prevent excessive resource usage

### State Management
- Efficient state preservation with automatic cleanup
- Minimal memory footprint
- Timestamp-based expiration

## Browser Support

- **History API**: Full support for modern browsers
- **Scroll Restoration**: Smooth scrolling with position memory
- **Deep Linking**: Full support for bookmarkable URLs
- **Back/Forward**: Proper browser navigation handling

## Testing

The routing system includes comprehensive tests:

- **Unit tests**: Core functionality and utilities
- **Integration tests**: End-to-end navigation flows
- **Error handling**: Network failures and edge cases
- **Performance**: Preloading and optimization features

Run tests with:
```bash
npm test -- --run routing
```

## Security Considerations

- **Return URL validation**: Only relative URLs allowed
- **MBTI parameter validation**: Strict validation against known types
- **Token validation**: JWT tokens validated before route access
- **State sanitization**: Sensitive data excluded from preserved state

## Future Enhancements

Potential improvements for future versions:

1. **Route Transitions**: Animated transitions between pages
2. **Breadcrumb Navigation**: Automatic breadcrumb generation
3. **Route Caching**: Advanced caching strategies
4. **Analytics Integration**: Route-based analytics tracking
5. **A/B Testing**: Route-based feature flags

## Troubleshooting

### Common Issues

**Route not found**: Check route definitions in `src/router/index.ts`
**Authentication loops**: Verify token validation logic
**State not preserved**: Check component lifecycle hooks
**Preloading not working**: Verify directive registration in `main.ts`

### Debug Mode

Enable router debugging:
```typescript
const router = createRouter({
  // ... config
})

if (import.meta.env.DEV) {
  router.beforeEach((to, from) => {
    console.log(`Navigation: ${from.path} → ${to.path}`)
  })
}
```

## Implementation Status

✅ **Completed Features:**
- Vue Router configuration with authentication guards
- Route definitions for all required pages
- Navigation composable with state preservation
- Browser history management and deep linking
- Route-based code splitting and preloading
- Comprehensive error handling
- MBTI parameter validation
- Scroll behavior management
- Performance optimizations
- Test coverage

This implementation fully satisfies the requirements specified in task 20 of the MBTI Travel Web Frontend specification.