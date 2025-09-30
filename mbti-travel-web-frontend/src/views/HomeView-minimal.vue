<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const selectedPersonality = ref('')

const personalityTypes = [
  { code: 'INTJ', name: 'The Architect', description: 'Strategic and analytical' },
  { code: 'INTP', name: 'The Thinker', description: 'Innovative and curious' },
  { code: 'ENTJ', name: 'The Commander', description: 'Bold and decisive' },
  { code: 'ENTP', name: 'The Debater', description: 'Smart and energetic' },
  { code: 'INFJ', name: 'The Advocate', description: 'Creative and insightful' },
  { code: 'INFP', name: 'The Mediator', description: 'Poetic and kind' },
  { code: 'ENFJ', name: 'The Protagonist', description: 'Charismatic and inspiring' },
  { code: 'ENFP', name: 'The Campaigner', description: 'Enthusiastic and creative' },
  { code: 'ISTJ', name: 'The Logistician', description: 'Practical and fact-minded' },
  { code: 'ISFJ', name: 'The Protector', description: 'Warm and responsible' },
  { code: 'ESTJ', name: 'The Executive', description: 'Organized and driven' },
  { code: 'ESFJ', name: 'The Consul', description: 'Caring and social' },
  { code: 'ISTP', name: 'The Virtuoso', description: 'Bold and practical' },
  { code: 'ISFP', name: 'The Adventurer', description: 'Flexible and charming' },
  { code: 'ESTP', name: 'The Entrepreneur', description: 'Smart and energetic' },
  { code: 'ESFP', name: 'The Entertainer', description: 'Spontaneous and enthusiastic' }
]

function generateItinerary() {
  if (!selectedPersonality.value) {
    alert('Please select your personality type first!')
    return
  }
  
  // For now, just show an alert with the selected personality
  alert(`Great! Generating a personalized Hong Kong itinerary for ${selectedPersonality.value} personality type. This feature is coming soon!`)
}

function takeMBTITest() {
  window.open('https://www.16personalities.com/free-personality-test', '_blank')
}
</script>

<template>
  <div class="home-view">
    <div class="welcome-section">
      <h2>Welcome to Your Personalized Travel Experience</h2>
      <p>Select your MBTI personality type to get a customized Hong Kong itinerary</p>
    </div>

    <div class="personality-selector">
      <h3>Choose Your Personality Type</h3>
      
      <div class="mbti-test-link">
        <p>Don't know your personality type?</p>
        <button @click="takeMBTITest" class="test-button">
          Take the Free MBTI Test
        </button>
      </div>

      <div class="personality-grid">
        <div 
          v-for="type in personalityTypes" 
          :key="type.code"
          class="personality-card"
          :class="{ selected: selectedPersonality === type.code }"
          @click="selectedPersonality = type.code"
        >
          <h4>{{ type.code }}</h4>
          <h5>{{ type.name }}</h5>
          <p>{{ type.description }}</p>
        </div>
      </div>

      <div class="action-section" v-if="selectedPersonality">
        <p>Selected: <strong>{{ selectedPersonality }}</strong></p>
        <button @click="generateItinerary" class="generate-button">
          Generate My Hong Kong Itinerary
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 3rem;
}

.welcome-section h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: white;
}

.welcome-section p {
  font-size: 1.1rem;
  opacity: 0.9;
}

.personality-selector h3 {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: white;
}

.mbti-test-link {
  text-align: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.test-button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.test-button:hover {
  background: #45a049;
}

.personality-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.personality-card {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.personality-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.personality-card.selected {
  border-color: #4CAF50;
  background: rgba(76, 175, 80, 0.2);
}

.personality-card h4 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
  color: #4CAF50;
}

.personality-card h5 {
  font-size: 1.1rem;
  margin: 0 0 0.5rem 0;
  color: white;
}

.personality-card p {
  margin: 0;
  opacity: 0.8;
  font-size: 0.9rem;
}

.action-section {
  text-align: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  backdrop-filter: blur(10px);
}

.action-section p {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.generate-button {
  background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 25px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.generate-button:hover {
  transform: scale(1.05);
}

@media (max-width: 768px) {
  .personality-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-section h2 {
    font-size: 1.5rem;
  }
  
  .generate-button {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }
}
</style>