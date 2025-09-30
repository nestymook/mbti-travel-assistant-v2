<template>
  <div class="group-notes-component">
    <div class="notes-header">
      <h3 class="notes-title">👥 Group Notes & Sharing</h3>
      <button @click="addNote" class="add-note-btn">+ Add Note</button>
    </div>
    <div class="notes-list">
      <div
        v-for="(note, index) in notes"
        :key="note.id"
        class="note-item"
      >
        <div class="note-header">
          <input
            v-model="note.author"
            type="text"
            class="note-author"
            placeholder="Your name"
          />
          <span class="note-date">{{ formatDate(note.date) }}</span>
          <button @click="removeNote(index)" class="remove-note-btn">×</button>
        </div>
        <textarea
          v-model="note.content"
          class="note-content"
          placeholder="Share your thoughts, suggestions, or memories..."
          @input="updateNotes"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface GroupNote {
  id: string
  author: string
  content: string
  date: Date
}

const props = defineProps<{
  initialNotes?: GroupNote[]
}>()

const emit = defineEmits<{
  notesUpdate: [notes: GroupNote[]]
}>()

const notes = ref<GroupNote[]>(props.initialNotes || [])

function addNote() {
  notes.value.push({
    id: Date.now().toString(),
    author: '',
    content: '',
    date: new Date()
  })
  updateNotes()
}

function removeNote(index: number) {
  notes.value.splice(index, 1)
  updateNotes()
}

function updateNotes() {
  emit('notesUpdate', notes.value)
}

function formatDate(date: Date): string {
  return date.toLocaleDateString()
}
</script>

<style scoped>
.group-notes-component {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 1rem 0;
}

.notes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.notes-title {
  color: #856404;
  margin: 0;
  font-size: 1.2rem;
}

.add-note-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.note-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
}

.note-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.note-author {
  flex: 1;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

.note-date {
  color: #6c757d;
  font-size: 0.8rem;
}

.remove-note-btn {
  background: #dc3545;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
}

.note-content {
  width: 100%;
  min-height: 60px;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-family: inherit;
  resize: vertical;
}
</style>