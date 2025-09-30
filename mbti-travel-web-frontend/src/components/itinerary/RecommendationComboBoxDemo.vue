<template>
  <div class="demo-container">
    <h2>RecommendationComboBox Demo</h2>
    
    <div class="demo-section">
      <h3>Restaurant Selection</h3>
      <RecommendationComboBox
        v-model="selectedRestaurant"
        :options="restaurants"
        type="restaurant"
        :mbti-personality="mbtiPersonality"
        label="Select a Restaurant"
        description="Choose from available restaurants"
        placeholder="Pick your restaurant..."
        :is-loading="isLoadingRestaurants"
        @selection-changed="onRestaurantChanged"
      />
      
      <div v-if="selectedRestaurant" class="selection-info">
        <h4>Selected Restaurant:</h4>
        <pre>{{ JSON.stringify(selectedRestaurant, null, 2) }}</pre>
      </div>
    </div>

    <div class="demo-section">
      <h3>Tourist Spot Selection</h3>
      <RecommendationComboBox
        v-model="selectedTouristSpot"
        :options="touristSpots"
        type="tourist-spot"
        :mbti-personality="mbtiPersonality"
        label="Select a Tourist Spot"
        description="Choose from available tourist spots"
        placeholder="Pick your destination..."
        :is-loading="isLoadingTouristSpots"
        @selection-changed="onTouristSpotChanged"
      />
      
      <div v-if="selectedTouristSpot" class="selection-info">
        <h4>Selected Tourist Spot:</h4>
        <pre>{{ JSON.stringify(selectedTouristSpot, null, 2) }}</pre>
      </div>
    </div>

    <div class="demo-controls">
      <h3>Demo Controls</h3>
      <div class="control-group">
        <label for="mbti-select">MBTI Personality:</label>
        <select id="mbti-select" v-model="mbtiPersonality">
          <option v-for="personality in mbtiTypes" :key="personality" :value="personality">
            {{ personality }}
          </option>
        </select>
      </div>
      
      <div class="control-group">
        <button @click="toggleRestaurantLoading">
          {{ isLoadingRestaurants ? 'Stop' : 'Start' }} Restaurant Loading
        </button>
        <button @click="toggleTouristSpotLoading">
          {{ isLoadingTouristSpots ? 'Stop' : 'Start' }} Tourist Spot Loading
        </button>
      </div>
      
      <div class="control-group">
        <button @click="clearSelections">Clear All Selections</button>
        <button @click="randomizeSelections">Random Selections</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import RecommendationComboBox from './RecommendationComboBox.vue'
import type { Restaurant } from '@/types/restaurant'
import type { TouristSpot } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'

// Demo data
const restaurants: Restaurant[] = [
  {
    id: 'rest-001',
    name: 'Tim Ho Wan',
    address: '2-20 Kwong Wa St, Mong Kok',
    mealType: ['breakfast', 'lunch'],
    sentiment: { likes: 85, dislikes: 10, neutral: 5 },
    locationCategory: 'Kowloon',
    district: 'Yau Tsim Mong',
    priceRange: 'budget',
    operatingHours: {
      'Mon - Fri': '06:00-14:30',
      'Sat - Sun': '06:00-16:00',
      'Public Holiday': '06:00-16:00'
    }
  },
  {
    id: 'rest-002',
    name: 'Lung King Heen',
    address: 'Four Seasons Hotel, 8 Finance St',
    mealType: ['lunch', 'dinner'],
    sentiment: { likes: 95, dislikes: 2, neutral: 3 },
    locationCategory: 'Hong Kong Island',
    district: 'Central and Western',
    priceRange: 'luxury',
    operatingHours: {
      'Mon - Fri': '12:00-14:30, 18:00-22:30',
      'Sat - Sun': '11:30-15:00, 18:00-22:30',
      'Public Holiday': '11:30-15:00, 18:00-22:30'
    }
  },
  {
    id: 'rest-003',
    name: 'Yung Kee Restaurant',
    address: '32-40 Wellington St, Central',
    mealType: ['lunch', 'dinner'],
    sentiment: { likes: 78, dislikes: 15, neutral: 7 },
    locationCategory: 'Hong Kong Island',
    district: 'Central and Western',
    priceRange: 'moderate',
    operatingHours: {
      'Mon - Fri': '11:00-23:30',
      'Sat - Sun': '11:00-23:30',
      'Public Holiday': '11:00-23:30'
    }
  }
]

const touristSpots: TouristSpot[] = [
  {
    tourist_spot: 'Victoria Peak',
    mbti: 'ENFP',
    description: 'Iconic Hong Kong viewpoint with stunning city skyline views',
    address: '1 Peak Rd, The Peak',
    district: 'Central and Western',
    area: 'The Peak',
    operating_hours_mon_fri: '10:00-23:00',
    operating_hours_sat_sun: '08:00-23:00',
    operating_hours_public_holiday: '08:00-23:00',
    full_day: false,
    remarks: 'Best views of Hong Kong skyline, take the Peak Tram'
  },
  {
    tourist_spot: 'Temple Street Night Market',
    mbti: 'ESTP',
    description: 'Bustling night market with street food and shopping',
    address: 'Temple St, Yau Ma Tei',
    district: 'Yau Tsim Mong',
    area: 'Yau Ma Tei',
    operating_hours_mon_fri: '18:00-24:00',
    operating_hours_sat_sun: '18:00-24:00',
    operating_hours_public_holiday: '18:00-24:00',
    full_day: false,
    remarks: 'Street food, fortune telling, and local atmosphere'
  },
  {
    tourist_spot: 'Hong Kong Museum of History',
    mbti: 'INTJ',
    description: 'Comprehensive museum showcasing Hong Kong\'s rich history',
    address: '100 Chatham Rd S, Tsim Sha Tsui East',
    district: 'Yau Tsim Mong',
    area: 'Tsim Sha Tsui',
    operating_hours_mon_fri: '10:00-18:00',
    operating_hours_sat_sun: '10:00-19:00',
    operating_hours_public_holiday: '10:00-19:00',
    full_day: true,
    remarks: 'Closed on Tuesdays, excellent for history enthusiasts'
  }
]

const mbtiTypes: MBTIPersonality[] = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

// Reactive state
const selectedRestaurant = ref<Restaurant | null>(null)
const selectedTouristSpot = ref<TouristSpot | null>(null)
const mbtiPersonality = ref<MBTIPersonality>('ENFP')
const isLoadingRestaurants = ref(false)
const isLoadingTouristSpots = ref(false)

// Event handlers
const onRestaurantChanged = (value: TouristSpot | Restaurant | null) => {
  console.log('Restaurant changed:', value)
}

const onTouristSpotChanged = (value: TouristSpot | Restaurant | null) => {
  console.log('Tourist spot changed:', value)
}

// Demo controls
const toggleRestaurantLoading = () => {
  isLoadingRestaurants.value = !isLoadingRestaurants.value
}

const toggleTouristSpotLoading = () => {
  isLoadingTouristSpots.value = !isLoadingTouristSpots.value
}

const clearSelections = () => {
  selectedRestaurant.value = null
  selectedTouristSpot.value = null
}

const randomizeSelections = () => {
  const randomRestaurantIndex = Math.floor(Math.random() * restaurants.length)
  const randomTouristSpotIndex = Math.floor(Math.random() * touristSpots.length)
  
  selectedRestaurant.value = restaurants[randomRestaurantIndex] || null
  selectedTouristSpot.value = touristSpots[randomTouristSpotIndex] || null
}
</script>

<style scoped>
.demo-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

.demo-section {
  margin-bottom: 3rem;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #f9fafb;
}

.demo-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #374151;
}

.selection-info {
  margin-top: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 0.375rem;
  border: 1px solid #d1d5db;
}

.selection-info h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: #111827;
}

.selection-info pre {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  white-space: pre-wrap;
  word-break: break-word;
}

.demo-controls {
  padding: 1.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  background: white;
}

.demo-controls h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #374151;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-group label {
  font-weight: 500;
  color: #374151;
  min-width: 120px;
}

.control-group select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 0.875rem;
}

.control-group button {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.control-group button:hover {
  background: #2563eb;
}

.control-group button:active {
  background: #1d4ed8;
}

/* Responsive design */
@media (max-width: 768px) {
  .demo-container {
    padding: 1rem;
  }
  
  .control-group {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .control-group label {
    min-width: auto;
  }
}
</style>