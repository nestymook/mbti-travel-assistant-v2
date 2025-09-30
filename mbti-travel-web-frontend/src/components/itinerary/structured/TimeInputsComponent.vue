<template>
  <div class="time-inputs-component">
    <div class="time-section">
      <h3 class="time-title">Schedule Management</h3>
      <div class="time-controls">
        <div class="time-input-group">
          <label for="start-time" class="time-label">Start Time:</label>
          <input
            id="start-time"
            v-model="startTime"
            type="time"
            class="time-input"
            @change="updateSchedule"
          />
        </div>
        <div class="time-input-group">
          <label for="end-time" class="time-label">End Time:</label>
          <input
            id="end-time"
            v-model="endTime"
            type="time"
            class="time-input"
            @change="updateSchedule"
          />
        </div>
        <div class="time-input-group">
          <label for="duration" class="time-label">Duration (hours):</label>
          <input
            id="duration"
            v-model.number="duration"
            type="number"
            min="0.5"
            max="24"
            step="0.5"
            class="time-input"
            @change="updateSchedule"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface TimeSchedule {
  startTime: string
  endTime: string
  duration: number
}

const props = defineProps<{
  initialSchedule?: TimeSchedule
}>()

const emit = defineEmits<{
  scheduleUpdate: [schedule: TimeSchedule]
}>()

const startTime = ref(props.initialSchedule?.startTime || '09:00')
const endTime = ref(props.initialSchedule?.endTime || '17:00')
const duration = ref(props.initialSchedule?.duration || 8)

const schedule = computed((): TimeSchedule => ({
  startTime: startTime.value,
  endTime: endTime.value,
  duration: duration.value
}))

function updateSchedule() {
  emit('scheduleUpdate', schedule.value)
}

// Auto-calculate duration when times change
watch([startTime, endTime], () => {
  if (startTime.value && endTime.value) {
    const start = new Date(`2000-01-01T${startTime.value}`)
    const end = new Date(`2000-01-01T${endTime.value}`)
    const diffMs = end.getTime() - start.getTime()
    const diffHours = diffMs / (1000 * 60 * 60)
    
    if (diffHours > 0) {
      duration.value = Math.round(diffHours * 2) / 2 // Round to nearest 0.5
    }
  }
})
</script>

<style scoped>
.time-inputs-component {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  margin: 0.5rem 0;
}

.time-title {
  color: #495057;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
}

.time-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.time-label {
  font-weight: 500;
  color: #495057;
  font-size: 0.9rem;
}

.time-input {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
  transition: border-color 0.2s ease;
}

.time-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}
</style>