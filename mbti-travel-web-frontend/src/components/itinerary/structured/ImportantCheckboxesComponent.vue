<template>
  <div class="important-checkboxes-component">
    <div class="checkbox-section">
      <h3 class="checkbox-title">Priority Items</h3>
      <div class="checkbox-grid">
        <div
          v-for="item in checkboxItems"
          :key="item.id"
          class="checkbox-item"
          :class="{ 'high-priority': item.priority === 'high' }"
        >
          <label class="checkbox-label">
            <input
              v-model="item.checked"
              type="checkbox"
              class="checkbox-input"
              @change="updateCheckedItems"
            />
            <span class="checkbox-custom"></span>
            <span class="checkbox-text">{{ item.label }}</span>
            <span v-if="item.priority === 'high'" class="priority-badge">!</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface CheckboxItem {
  id: string
  label: string
  checked: boolean
  priority: 'normal' | 'high'
}

const props = defineProps<{
  items?: CheckboxItem[]
}>()

const emit = defineEmits<{
  itemsUpdate: [items: CheckboxItem[]]
}>()

const checkboxItems = ref<CheckboxItem[]>(props.items || [
  { id: '1', label: 'Confirm reservations', checked: false, priority: 'high' },
  { id: '2', label: 'Check weather forecast', checked: false, priority: 'normal' },
  { id: '3', label: 'Pack essentials', checked: false, priority: 'high' },
  { id: '4', label: 'Charge devices', checked: false, priority: 'normal' }
])

function updateCheckedItems() {
  emit('itemsUpdate', checkboxItems.value)
}
</script>

<style scoped>
.important-checkboxes-component {
  background: #fff8e1;
  border: 1px solid #ffcc02;
  border-radius: 8px;
  padding: 1rem;
  margin: 0.5rem 0;
}

.checkbox-title {
  color: #e65100;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-input {
  margin-right: 0.5rem;
}

.checkbox-text {
  flex: 1;
}
</style>