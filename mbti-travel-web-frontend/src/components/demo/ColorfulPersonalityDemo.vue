<template>
  <div class="colorful-personality-demo">
    <div class="demo-header">
      <h2>Colorful Personality Type Customizations</h2>
      <p>Experience vibrant themes and image placeholders for creative personalities</p>
    </div>

    <div class="personality-selector">
      <label for="personality-select">Select Personality Type:</label>
      <select 
        id="personality-select"
        v-model="selectedPersonality"
        class="personality-select"
        @change="onPersonalityChange"
      >
        <option value="">Choose a personality...</option>
        <optgroup label="Colorful Personalities">
          <option value="ENTP">ENTP - The Debater</option>
          <option value="INFP">INFP - The Mediator</option>
          <option value="ENFP">ENFP - The Campaigner</option>
          <option value="ISFP">ISFP - The Adventurer</option>
        </optgroup>
        <optgroup label="Other Creative Types">
          <option value="ESTP">ESTP - The Entrepreneur (Flashy)</option>
          <option value="ESFP">ESFP - The Entertainer</option>
        </optgroup>
        <optgroup label="Comparison Types">
          <option value="INTJ">INTJ - The Architect (Structured)</option>
          <option value="ISFJ">ISFJ - The Protector (Warm)</option>
        </optgroup>
      </select>
    </div>

    <div v-if="selectedPersonality" class="demo-content" :class="personalityClass">
      <div class="theme-showcase">
        <h3>Theme Colors</h3>
        <div class="color-palette">
          <div class="color-swatch primary">
            <div class="color-box"></div>
            <span>Primary</span>
          </div>
          <div class="color-swatch secondary">
            <div class="color-box"></div>
            <span>Secondary</span>
          </div>
          <div class="color-swatch accent">
            <div class="color-box"></div>
            <span>Accent</span>
          </div>
        </div>
      </div>

      <div v-if="shouldShowImages" class="image-showcase">
        <h3>Image Placeholders</h3>
        <div class="image-gallery">
          <ImagePlaceholder
            :mbti-personality="selectedPersonality"
            title="Tourist Attraction"
            subtitle="Stunning views await"
            size="medium"
            variant="spot"
            @click="handleImageClick"
          />
          <ImagePlaceholder
            :mbti-personality="selectedPersonality"
            title="Restaurant"
            subtitle="Delicious cuisine"
            size="medium"
            variant="restaurant"
            @click="handleImageClick"
          />
          <ImagePlaceholder
            :mbti-personality="selectedPersonality"
            title="Photo Gallery"
            subtitle="Memorable moments"
            size="medium"
            variant="gallery"
            @click="handleImageClick"
          />
        </div>
      </div>

      <div class="features-showcase">
        <h3>Visual Enhancements</h3>
        <div class="feature-cards">
          <div class="feature-card">
            <h4>Vibrant Colors</h4>
            <p>Dynamic color schemes that reflect your creative personality</p>
          </div>
          <div class="feature-card">
            <h4>Gradient Backgrounds</h4>
            <p>Beautiful gradient overlays and animated effects</p>
          </div>
          <div v-if="isColorfulPersonality" class="feature-card">
            <h4>Creative Elements</h4>
            <p>Sparkles, animations, and visual flair for artistic types</p>
          </div>
          <div v-if="selectedPersonality === 'ESTP'" class="feature-card flashy">
            <h4>Flashy Styling</h4>
            <p>Extra dynamic effects for the energetic ESTP personality</p>
          </div>
        </div>
      </div>

      <div class="sample-content">
        <h3>Sample Itinerary Content</h3>
        <div class="sample-table">
          <table class="demo-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>Day 1</th>
                <th>Day 2</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="session-label">Morning</td>
                <td class="recommendation-cell">
                  <select class="combo-box">
                    <option>Victoria Peak</option>
                    <option>Star Ferry</option>
                  </select>
                </td>
                <td class="recommendation-cell">
                  <select class="combo-box">
                    <option>Temple Street Market</option>
                    <option>Symphony of Lights</option>
                  </select>
                </td>
              </tr>
              <tr>
                <td class="session-label">Lunch</td>
                <td class="recommendation-cell">
                  <select class="combo-box">
                    <option>Dim Sum Restaurant</option>
                    <option>Local Cha Chaan Teng</option>
                  </select>
                </td>
                <td class="recommendation-cell">
                  <select class="combo-box">
                    <option>Rooftop Restaurant</option>
                    <option>Street Food Market</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="!selectedPersonality" class="placeholder-content">
      <p>Select a personality type above to see the colorful customizations in action!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import { ThemeService } from '@/services/themeService'
import ImagePlaceholder from '@/components/common/ImagePlaceholder.vue'

// Reactive state
const selectedPersonality = ref<MBTIPersonality | ''>('')
const themeService = ThemeService.getInstance()

// Computed properties
const personalityClass = computed(() => {
  if (!selectedPersonality.value) return ''
  return `mbti-${selectedPersonality.value.toLowerCase()}`
})

const isColorfulPersonality = computed(() => {
  if (!selectedPersonality.value) return false
  return themeService.isColorfulPersonality(selectedPersonality.value)
})

const shouldShowImages = computed(() => {
  if (!selectedPersonality.value) return false
  return themeService.shouldShowImages(selectedPersonality.value)
})

// Methods
const onPersonalityChange = () => {
  if (selectedPersonality.value) {
    themeService.applyMBTITheme(selectedPersonality.value)
  } else {
    themeService.resetTheme()
  }
}

const handleImageClick = () => {
  console.log(`🎉 Image clicked for ${selectedPersonality.value}!`)
  // In a real app, this would open an image gallery
}

// Lifecycle
onMounted(() => {
  // Set default personality for demo
  selectedPersonality.value = 'ENFP'
  onPersonalityChange()
})
</script>

<style scoped>
.colorful-personality-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.demo-header {
  text-align: center;
  margin-bottom: 2rem;
}

.demo-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--mbti-primary, #2c3e50);
  margin-bottom: 0.5rem;
}

.demo-header p {
  font-size: 1.1rem;
  color: var(--mbti-text, #6b7280);
  margin: 0;
}

.personality-selector {
  margin-bottom: 2rem;
  text-align: center;
}

.personality-selector label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--mbti-text, #374151);
}

.personality-select {
  padding: 0.75rem 1rem;
  border: 2px solid var(--mbti-border, #d1d5db);
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  color: var(--mbti-text, #374151);
  min-width: 300px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.personality-select:focus {
  outline: none;
  border-color: var(--mbti-primary, #3b82f6);
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(59, 130, 246, 0.1));
}

.demo-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  transition: all 0.3s ease;
}

.theme-showcase {
  background: var(--mbti-surface, white);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.theme-showcase h3 {
  margin: 0 0 1rem 0;
  color: var(--mbti-primary, #374151);
  font-size: 1.25rem;
  font-weight: 600;
}

.color-palette {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.color-swatch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.color-box {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.primary .color-box {
  background: var(--mbti-primary, #3b82f6);
}

.secondary .color-box {
  background: var(--mbti-secondary, #6b7280);
}

.accent .color-box {
  background: var(--mbti-accent, #10b981);
}

.color-swatch span {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--mbti-text, #6b7280);
}

.image-showcase {
  background: var(--mbti-surface, white);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.image-showcase h3 {
  margin: 0 0 1rem 0;
  color: var(--mbti-primary, #374151);
  font-size: 1.25rem;
  font-weight: 600;
}

.image-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.features-showcase {
  background: var(--mbti-surface, white);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.features-showcase h3 {
  margin: 0 0 1rem 0;
  color: var(--mbti-primary, #374151);
  font-size: 1.25rem;
  font-weight: 600;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.feature-card {
  padding: 1rem;
  background: var(--mbti-background, #f9fafb);
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #e5e7eb);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.feature-card.flashy {
  animation: flashy-pulse 2s ease-in-out infinite;
}

@keyframes flashy-pulse {
  0%, 100% {
    box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  }
  50% {
    box-shadow: 0 8px 16px var(--mbti-accent, #10b981);
  }
}

.feature-card h4 {
  margin: 0 0 0.5rem 0;
  color: var(--mbti-primary, #374151);
  font-size: 1rem;
  font-weight: 600;
}

.feature-card p {
  margin: 0;
  color: var(--mbti-text, #6b7280);
  font-size: 0.875rem;
  line-height: 1.5;
}

.sample-content {
  background: var(--mbti-surface, white);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.sample-content h3 {
  margin: 0 0 1rem 0;
  color: var(--mbti-primary, #374151);
  font-size: 1.25rem;
  font-weight: 600;
}

.demo-table {
  width: 100%;
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.demo-table th {
  background: var(--mbti-primary, #3b82f6);
  color: white;
  padding: 1rem;
  text-align: center;
  font-weight: 600;
}

.demo-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--mbti-border, #e5e7eb);
}

.session-label {
  background: var(--mbti-background, #f9fafb);
  color: var(--mbti-primary, #374151);
  font-weight: 600;
  border-right: 2px solid var(--mbti-border, #e5e7eb);
}

.recommendation-cell {
  background: white;
}

.combo-box {
  width: 100%;
  padding: 0.5rem;
  border: 2px solid var(--mbti-border, #d1d5db);
  border-radius: 6px;
  background: white;
  color: var(--mbti-text, #374151);
  cursor: pointer;
  transition: all 0.3s ease;
}

.combo-box:hover {
  border-color: var(--mbti-primary, #3b82f6);
}

.combo-box:focus {
  outline: none;
  border-color: var(--mbti-primary, #3b82f6);
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(59, 130, 246, 0.1));
}

.placeholder-content {
  text-align: center;
  padding: 3rem;
  color: var(--mbti-text, #6b7280);
  font-size: 1.1rem;
}

/* Import colorful personality themes */
@import '../../styles/themes/colorful-personalities.css';

/* Responsive design */
@media (max-width: 768px) {
  .colorful-personality-demo {
    padding: 1rem;
  }
  
  .demo-header h2 {
    font-size: 1.5rem;
  }
  
  .personality-select {
    min-width: 250px;
  }
  
  .color-palette {
    flex-wrap: wrap;
  }
  
  .image-gallery {
    grid-template-columns: 1fr;
  }
  
  .feature-cards {
    grid-template-columns: 1fr;
  }
  
  .demo-table {
    font-size: 0.875rem;
  }
  
  .demo-table th,
  .demo-table td {
    padding: 0.75rem;
  }
}

@media (max-width: 480px) {
  .demo-header h2 {
    font-size: 1.25rem;
  }
  
  .personality-select {
    min-width: 200px;
  }
  
  .color-box {
    width: 50px;
    height: 50px;
  }
  
  .demo-table th,
  .demo-table td {
    padding: 0.5rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .feature-card.flashy {
    animation: none;
  }
  
  .feature-card:hover {
    transform: none;
  }
  
  .combo-box,
  .personality-select {
    transition: none;
  }
}
</style>