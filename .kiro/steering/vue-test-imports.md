---
inclusion: fileMatch
fileMatchPattern: '**/__tests__/**/*.test.ts'
---

# Vue Test File Import Guidelines

## Import Pattern Rules for Test Files

When writing test files for Vue components and services, follow these import patterns to ensure consistency and avoid potential module resolution issues:

### ❌ Avoid Using '@/' Alias in Test Files

```typescript
// DON'T - Avoid '@/' alias in test files
import InputPage from '@/views/InputPage.vue'
import { ValidationService, ApiService } from '@/services'
import type { MBTIPersonality } from '@/types'
```

### ✅ Use Relative Imports in Test Files

```typescript
// DO - Use relative imports for better test reliability
import InputPage from '../InputPage.vue'
import { ValidationService, ApiService } from '../../services'
import type { MBTIPersonality } from '../../types'
```

## Rationale

1. **Test Environment Compatibility**: Some test runners may have different module resolution behavior than the main application
2. **Explicit Dependencies**: Relative imports make the file structure and dependencies more explicit
3. **Reduced Configuration Dependency**: Less reliance on build tool configuration for path resolution
4. **Better IDE Support**: Some IDEs handle relative imports more reliably in test contexts

## Exceptions

The '@/' alias pattern may be acceptable in test files when:
- The relative path becomes excessively long (more than 3 levels: `../../../..`)
- The test configuration explicitly supports and requires alias usage
- Working with shared test utilities that are designed to use aliases

## Examples

### Component Test File Structure
```
src/
├── components/
│   ├── input/
│   │   ├── MBTIInputForm.vue
│   │   └── __tests__/
│   │       └── MBTIInputForm.test.ts  // Use '../MBTIInputForm.vue'
│   └── itinerary/
│       ├── ItineraryHeader.vue
│       └── __tests__/
│           └── ItineraryHeader.test.ts  // Use '../ItineraryHeader.vue'
├── views/
│   ├── InputPage.vue
│   └── __tests__/
│       └── InputPage.test.ts  // Use '../InputPage.vue'
└── services/
    ├── apiService.ts
    └── __tests__/
        └── apiService.test.ts  // Use '../apiService.ts'
```

### Correct Import Patterns by Location

#### Component Tests (`src/components/*/__tests__/*.test.ts`)
```typescript
import ComponentName from '../ComponentName.vue'
import { ServiceName } from '../../../services'
import type { TypeName } from '../../../types'
```

#### View Tests (`src/views/__tests__/*.test.ts`)
```typescript
import ViewName from '../ViewName.vue'
import { ServiceName } from '../../services'
import type { TypeName } from '../../types'
```

#### Service Tests (`src/services/__tests__/*.test.ts`)
```typescript
import { ServiceName } from '../serviceName'
import type { TypeName } from '../../types'
```

## Migration Guide

If you encounter existing test files using '@/' aliases, update them as follows:

1. **Identify the current file location** relative to `src/`
2. **Calculate the relative path** to the target file
3. **Replace '@/' with the appropriate '../' pattern**

### Example Migration
```typescript
// Before (in src/views/__tests__/InputPage.test.ts)
import InputPage from '@/views/InputPage.vue'
import { ValidationService } from '@/services'

// After
import InputPage from '../InputPage.vue'
import { ValidationService } from '../../services'
```

## Testing Import Resolution

To verify your imports are working correctly:

1. **Run the specific test file**: `npm run test -- --run path/to/test.ts`
2. **Check for import errors** in the test output
3. **Verify IDE intellisense** works with the relative imports
4. **Ensure build process** handles the imports correctly

This approach ensures maximum compatibility across different test environments and build configurations while maintaining clear, explicit import relationships.