<template>
  <div class="descriptions-component">
    <div class="description-header">
      <h3 class="description-title">💭 Detailed Descriptions</h3>
    </div>
    <div class="descriptions-list">
      <div
        v-for="(item, index) in descriptions"
        :key="index"
        class="description-item"
      >
        <div class="description-label">{{ item.label }}</div>
        <textarea
          v-model="item.text"
          class="description-textarea"
          :placeholder="item.placeholder"
          @input="updateDescriptions"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Description {
  label: string
  text: string
  placeholder: string
}

const props = defineProps<{
  initialDescriptions?: Description[]
}>()

const emit = defineEmits<{
  descriptionsUpdate: [descriptions: Description[]]
}>()

const descriptions = ref<Description[]>(props.initialDescriptions || [
  {
    label: 'Experience Goals',
    text: '',
    placeholder: 'What do you hope to experience or feel during this trip?'
  },
  {
    label: 'Personal Reflections',
    text: '',
    placeholder: 'What personal meaning does this journey have for you?'
  },
  {
    label: 'Memory Moments',
    text: '',
    placeholder: 'What moments do you want to remember most?'
  }
])

function updateDescriptions() {
  emit('descriptionsUpdate', descriptions.value)
}
</script>

<style scoped>
.descriptions-component {
  background: #f8f4ff;
  border: 1px solid #e1d5f7;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 1rem 0;
}

.description-header {
  margin-bottom: 1.5rem;
}

.description-title {
  color: #6f42c1;
  margin: 0;
  font-size: 1.2rem;
}

.descriptions-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.description-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.description-label {
  font-weight: 500;
  color: #495057;
  font-size: 0.95rem;
}

.description-textarea {
  min-height: 80px;
  padding: 0.75rem;
  border: 1px solid #d1ecf1;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.9rem;
  resize: vertical;
  background: white;
  transition: border-color 0.2s ease;
}

.description-textarea:focus {
  outline: none;
  border-color: #6f42c1;
  box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.25);
}

.description-textarea::placeholder {
  color: #6c757d;
  font-style: italic;
}
</style>