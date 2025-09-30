/**
 * Lazy-loaded personality-specific components
 * This file provides dynamic imports for personality-specific components
 * to enable code splitting and reduce initial bundle size
 */

import type { Component } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import { bundleOptimization } from '@/utils/performance'

// Component loader type
type ComponentLoader = () => Promise<{ default: Component }>

/**
 * Lazy component loaders for structured personalities (INTJ, ENTJ, ISTJ, ESTJ)
 * These personalities prefer time management features
 */
const structuredPersonalityLoaders: Record<string, ComponentLoader> = {
    'time-inputs': () => import('./structured/TimeInputsComponent.vue').then(m => m),
    'important-checkboxes': () => import('./structured/ImportantCheckboxesComponent.vue').then(m => m),
    'structured-layout': () => import('./structured/StructuredLayoutComponent.vue').then(m => m)
}

/**
 * Lazy component loaders for flexible personalities (INTP, ISTP, ESTP)
 * These personalities prefer point-form layouts
 */
const flexiblePersonalityLoaders: Record<string, ComponentLoader> = {
    'point-form': () => import('./flexible/PointFormComponent.vue').then(m => m),
    'casual-layout': () => import('./flexible/CasualLayoutComponent.vue').then(m => m),
    'flashy-styling': () => import('./flexible/FlashyStylingComponent.vue').then(m => m)
}

/**
 * Lazy component loaders for colorful personalities (ENTP, INFP, ENFP, ISFP, ESFP)
 * These personalities prefer vibrant, creative interfaces
 */
const colorfulPersonalityLoaders: Record<string, ComponentLoader> = {
    'vibrant-theme': () => import('./colorful/VibrantThemeComponent.vue').then(m => m),
    'image-placeholders': () => import('./colorful/ImagePlaceholdersComponent.vue').then(m => m),
    'creative-layout': () => import('./colorful/CreativeLayoutComponent.vue').then(m => m),
    'gradient-backgrounds': () => import('./colorful/GradientBackgroundsComponent.vue').then(m => m)
}

/**
 * Lazy component loaders for feeling personalities (INFJ, ISFJ, ENFJ, ESFJ)
 * These personalities prefer detailed descriptions and social features
 */
const feelingPersonalityLoaders: Record<string, ComponentLoader> = {
    'descriptions': () => import('./feeling/DescriptionsComponent.vue').then(m => m),
    'group-notes': () => import('./feeling/GroupNotesComponent.vue').then(m => m),
    'social-sharing': () => import('./feeling/SocialSharingComponent.vue').then(m => m),
    'warm-theme': () => import('./feeling/WarmThemeComponent.vue').then(m => m)
}

/**
 * Main personality component loaders
 * These are the primary layout components for each personality type
 */
const personalityLayoutLoaders: Record<MBTIPersonality, ComponentLoader> = {
    // Structured personalities
    'INTJ': () => import('./layouts/INTJLayout.vue').then(m => m),
    'ENTJ': () => import('./layouts/ENTJLayout.vue').then(m => m),
    'ISTJ': () => import('./layouts/ISTJLayout.vue').then(m => m),
    'ESTJ': () => import('./layouts/ESTJLayout.vue').then(m => m),

    // Flexible personalities
    'INTP': () => import('./layouts/INTPLayout.vue').then(m => m),
    'ISTP': () => import('./layouts/ISTPLayout.vue').then(m => m),
    'ESTP': () => import('./layouts/ESTPLayout.vue').then(m => m),

    // Colorful personalities
    'ENTP': () => import('./layouts/ENTPLayout.vue').then(m => m),
    'INFP': () => import('./layouts/INFPLayout.vue').then(m => m),
    'ENFP': () => import('./layouts/ENFPLayout.vue').then(m => m),
    'ISFP': () => import('./layouts/ISFPLayout.vue').then(m => m),
    'ESFP': () => import('./layouts/ESFPLayout.vue').then(m => m),

    // Feeling personalities
    'INFJ': () => import('./layouts/INFJLayout.vue').then(m => m),
    'ISFJ': () => import('./layouts/ISFJLayout.vue').then(m => m),
    'ENFJ': () => import('./layouts/ENFJLayout.vue').then(m => m),
    'ESFJ': () => import('./layouts/ESFJLayout.vue').then(m => m)
}

/**
 * Personality category mapping
 */
export const personalityCategories = {
    structured: ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'] as MBTIPersonality[],
    flexible: ['INTP', 'ISTP', 'ESTP'] as MBTIPersonality[],
    colorful: ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESFP'] as MBTIPersonality[],
    feeling: ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'] as MBTIPersonality[]
}

/**
 * Get personality category for a given MBTI type
 */
export function getPersonalityCategory(personality: MBTIPersonality): string {
    for (const [category, personalities] of Object.entries(personalityCategories)) {
        if (personalities.includes(personality)) {
            return category
        }
    }
    return 'default'
}

/**
 * Load main personality layout component
 */
export async function loadPersonalityLayout(personality: MBTIPersonality): Promise<Component | null> {
    const loader = personalityLayoutLoaders[personality]
    if (!loader) {
        console.warn(`No layout component found for personality: ${personality}`)
        return null
    }

    const module = await bundleOptimization.dynamicImport(loader)
    return module?.default || null
}

/**
 * Load personality-specific feature components
 */
export async function loadPersonalityFeatures(personality: MBTIPersonality): Promise<Record<string, Component>> {
    const category = getPersonalityCategory(personality)
    const features: Record<string, Component> = {}

    try {
        switch (category) {
            case 'structured':
                // Load structured personality features
                if (personality === 'ENTJ') {
                    const loader = structuredPersonalityLoaders['important-checkboxes']
                    if (loader) {
                        const module = await bundleOptimization.dynamicImport(loader)
                        features.importantCheckboxes = module?.default || {} as Component
                    }
                }
                const timeInputsLoader = structuredPersonalityLoaders['time-inputs']
                if (timeInputsLoader) {
                    const timeInputsModule = await bundleOptimization.dynamicImport(timeInputsLoader)
                    features.timeInputs = timeInputsModule?.default || {} as Component
                }

                const structuredLayoutLoader = structuredPersonalityLoaders['structured-layout']
                if (structuredLayoutLoader) {
                    const structuredLayoutModule = await bundleOptimization.dynamicImport(structuredLayoutLoader)
                    features.structuredLayout = structuredLayoutModule?.default || {} as Component
                }
                break

            case 'flexible':
                // Load flexible personality features
                const pointFormLoader = flexiblePersonalityLoaders['point-form']
                if (pointFormLoader) {
                    const pointFormModule = await bundleOptimization.dynamicImport(pointFormLoader)
                    features.pointForm = pointFormModule?.default || {} as Component
                }

                const casualLayoutLoader = flexiblePersonalityLoaders['casual-layout']
                if (casualLayoutLoader) {
                    const casualLayoutModule = await bundleOptimization.dynamicImport(casualLayoutLoader)
                    features.casualLayout = casualLayoutModule?.default || {} as Component
                }

                if (personality === 'ESTP') {
                    const flashyStylingLoader = flexiblePersonalityLoaders['flashy-styling']
                    if (flashyStylingLoader) {
                        const flashyStylingModule = await bundleOptimization.dynamicImport(flashyStylingLoader)
                        features.flashyStyling = flashyStylingModule?.default || {} as Component
                    }
                }
                break

            case 'colorful':
                // Load colorful personality features
                const vibrantThemeLoader = colorfulPersonalityLoaders['vibrant-theme']
                if (vibrantThemeLoader) {
                    const vibrantThemeModule = await bundleOptimization.dynamicImport(vibrantThemeLoader)
                    features.vibrantTheme = vibrantThemeModule?.default || {} as Component
                }

                const imagePlaceholdersLoader = colorfulPersonalityLoaders['image-placeholders']
                if (imagePlaceholdersLoader) {
                    const imagePlaceholdersModule = await bundleOptimization.dynamicImport(imagePlaceholdersLoader)
                    features.imagePlaceholders = imagePlaceholdersModule?.default || {} as Component
                }

                const creativeLayoutLoader = colorfulPersonalityLoaders['creative-layout']
                if (creativeLayoutLoader) {
                    const creativeLayoutModule = await bundleOptimization.dynamicImport(creativeLayoutLoader)
                    features.creativeLayout = creativeLayoutModule?.default || {} as Component
                }

                const gradientBackgroundsLoader = colorfulPersonalityLoaders['gradient-backgrounds']
                if (gradientBackgroundsLoader) {
                    const gradientBackgroundsModule = await bundleOptimization.dynamicImport(gradientBackgroundsLoader)
                    features.gradientBackgrounds = gradientBackgroundsModule?.default || {} as Component
                }
                break

            case 'feeling':
                // Load feeling personality features
                if (['INFJ', 'ISFJ'].includes(personality)) {
                    const descriptionsLoader = feelingPersonalityLoaders['descriptions']
                    if (descriptionsLoader) {
                        const descriptionsModule = await bundleOptimization.dynamicImport(descriptionsLoader)
                        features.descriptions = descriptionsModule?.default || {} as Component
                    }
                }

                if (['ENFJ', 'ESFJ'].includes(personality)) {
                    const groupNotesLoader = feelingPersonalityLoaders['group-notes']
                    if (groupNotesLoader) {
                        const groupNotesModule = await bundleOptimization.dynamicImport(groupNotesLoader)
                        features.groupNotes = groupNotesModule?.default || {} as Component
                    }

                    const socialSharingLoader = feelingPersonalityLoaders['social-sharing']
                    if (socialSharingLoader) {
                        const socialSharingModule = await bundleOptimization.dynamicImport(socialSharingLoader)
                        features.socialSharing = socialSharingModule?.default || {} as Component
                    }
                }

                if (personality === 'ISFJ') {
                    const warmThemeLoader = feelingPersonalityLoaders['warm-theme']
                    if (warmThemeLoader) {
                        const warmThemeModule = await bundleOptimization.dynamicImport(warmThemeLoader)
                        features.warmTheme = warmThemeModule?.default || {} as Component
                    }
                }
                break
        }
    } catch (error) {
        console.error(`Failed to load features for personality ${personality}:`, error)
    }

    return features
}

/**
 * Preload personality components for better performance
 */
export function preloadPersonalityComponents(personality: MBTIPersonality): void {
    // Preload main layout
    const layoutLoader = personalityLayoutLoaders[personality]
    if (layoutLoader) {
        layoutLoader().catch(error => {
            console.warn(`Failed to preload layout for ${personality}:`, error)
        })
    }

    // Preload category-specific features
    const category = getPersonalityCategory(personality)
    const loaders = getLoadersForCategory(category, personality)

    loaders.forEach(loader => {
        loader().catch(error => {
            console.warn(`Failed to preload component for ${personality}:`, error)
        })
    })
}

/**
 * Get component loaders for a specific category and personality
 */
function getLoadersForCategory(category: string, personality: MBTIPersonality): ComponentLoader[] {
    const loaders: ComponentLoader[] = []

    switch (category) {
        case 'structured':
            const timeInputsLoader = structuredPersonalityLoaders['time-inputs']
            const structuredLayoutLoader = structuredPersonalityLoaders['structured-layout']
            if (timeInputsLoader) loaders.push(timeInputsLoader)
            if (structuredLayoutLoader) loaders.push(structuredLayoutLoader)
            if (personality === 'ENTJ') {
                const importantCheckboxesLoader = structuredPersonalityLoaders['important-checkboxes']
                if (importantCheckboxesLoader) loaders.push(importantCheckboxesLoader)
            }
            break

        case 'flexible':
            const pointFormLoader = flexiblePersonalityLoaders['point-form']
            const casualLayoutLoader = flexiblePersonalityLoaders['casual-layout']
            if (pointFormLoader) loaders.push(pointFormLoader)
            if (casualLayoutLoader) loaders.push(casualLayoutLoader)
            if (personality === 'ESTP') {
                const flashyStylingLoader = flexiblePersonalityLoaders['flashy-styling']
                if (flashyStylingLoader) loaders.push(flashyStylingLoader)
            }
            break

        case 'colorful':
            const vibrantThemeLoader = colorfulPersonalityLoaders['vibrant-theme']
            const imagePlaceholdersLoader = colorfulPersonalityLoaders['image-placeholders']
            const creativeLayoutLoader = colorfulPersonalityLoaders['creative-layout']
            const gradientBackgroundsLoader = colorfulPersonalityLoaders['gradient-backgrounds']
            if (vibrantThemeLoader) loaders.push(vibrantThemeLoader)
            if (imagePlaceholdersLoader) loaders.push(imagePlaceholdersLoader)
            if (creativeLayoutLoader) loaders.push(creativeLayoutLoader)
            if (gradientBackgroundsLoader) loaders.push(gradientBackgroundsLoader)
            break

        case 'feeling':
            if (['INFJ', 'ISFJ'].includes(personality)) {
                const descriptionsLoader = feelingPersonalityLoaders['descriptions']
                if (descriptionsLoader) loaders.push(descriptionsLoader)
            }
            if (['ENFJ', 'ESFJ'].includes(personality)) {
                const groupNotesLoader = feelingPersonalityLoaders['group-notes']
                const socialSharingLoader = feelingPersonalityLoaders['social-sharing']
                if (groupNotesLoader) loaders.push(groupNotesLoader)
                if (socialSharingLoader) loaders.push(socialSharingLoader)
            }
            if (personality === 'ISFJ') {
                const warmThemeLoader = feelingPersonalityLoaders['warm-theme']
                if (warmThemeLoader) loaders.push(warmThemeLoader)
            }
            break
    }

    return loaders
}

/**
 * Component registry for tracking loaded components
 */
class ComponentRegistry {
    private loadedComponents = new Map<string, Component>()
    private loadingPromises = new Map<string, Promise<Component | null>>()

    async getComponent(key: string, loader: ComponentLoader): Promise<Component | null> {
        // Return cached component if available
        if (this.loadedComponents.has(key)) {
            return this.loadedComponents.get(key)!
        }

        // Return existing loading promise if in progress
        if (this.loadingPromises.has(key)) {
            return this.loadingPromises.get(key)!
        }

        // Start loading
        const loadingPromise = bundleOptimization.dynamicImport(loader)
        this.loadingPromises.set(key, loadingPromise)

        try {
            const module = await loadingPromise
            const component = module?.default || null
            if (component) {
                this.loadedComponents.set(key, component)
            }
            return component
        } catch (error) {
            console.error(`Failed to load component ${key}:`, error)
            return null
        } finally {
            this.loadingPromises.delete(key)
        }
    }

    clearCache(): void {
        this.loadedComponents.clear()
        this.loadingPromises.clear()
    }

    getCacheSize(): number {
        return this.loadedComponents.size
    }
}

// Export singleton registry
export const componentRegistry = new ComponentRegistry()

/**
 * Utility function to get component with caching
 */
export async function getPersonalityComponent(
    personality: MBTIPersonality,
    componentType: string
): Promise<Component | null> {
    const key = `${personality}-${componentType}`

    // Get appropriate loader
    let loader: ComponentLoader | undefined

    if (componentType === 'layout') {
        loader = personalityLayoutLoaders[personality]
    } else {
        const category = getPersonalityCategory(personality)
        const loaders = {
            structured: structuredPersonalityLoaders,
            flexible: flexiblePersonalityLoaders,
            colorful: colorfulPersonalityLoaders,
            feeling: feelingPersonalityLoaders
        }[category]

        loader = loaders?.[componentType]
    }

    if (!loader) {
        console.warn(`No loader found for ${personality} ${componentType}`)
        return null
    }

    return componentRegistry.getComponent(key, loader)
}

/**
 * Cleanup function for memory management
 */
export function cleanupPersonalityComponents(): void {
    componentRegistry.clearCache()
}