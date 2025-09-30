<template>
  <div class="point-form-component">
    <div class="point-form-header">
      <h3 class="form-title">Quick Points</h3>
      <button @click="addPoint" class="add-btn">+ Add Point</button>
    </div>
    <div class="points-list">
      <div
        v-for="(point, index) in points"
        :key="point.id"
        class="point-item"
      >
        <span class="point-bullet">•</span>
        <input
          v-model="point.text"
          type="text"
          class="point-input"
          placeholder="Enter point..."
          @input="updatePoints"
        />
        <button @click="removePoint(index)" class="remove-btn">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Point {
  id: string
  text: string
}

const props = defineProps<{
  initialPoints?: Point[]
}>()

const emit = defineEmits<{
  pointsUpdate: [points: Point[]]
}>()

const points = ref<Point[]>(props.initialPoints || [
  { id: '1', text: '' }
])

function addPoint() {
  points.value.push({
    id: Date.now().toString(),
    text: ''
  })
  updatePoints()
}

function removePoint(index: number) {
  points.value.splice(index, 1)
  updatePoints()
}

function updatePoints() {
  emit('pointsUpdate', points.value)
}
</script>

<style scoped>
.point-form-component {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 1rem;
  margin: 0.5rem 0;
}

.point-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.form-title {
  margin: 0;
  color: #333;
}

.add-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.points-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.point-bullet {
  color: #666;
  font-weight: bold;
}

.point-input {
  flex: 1;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.remove-btn {
  background: #dc3545;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
}
</style>