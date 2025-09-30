#!/usr/bin/env node

/**
 * Script to create placeholder layout components for all MBTI personalities
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const personalities = [
  { type: 'ENTJ', name: 'The Commander' },
  { type: 'ISTJ', name: 'The Logistician' },
  { type: 'ESTJ', name: 'The Executive' },
  { type: 'INTP', name: 'The Thinker' },
  { type: 'ISTP', name: 'The Virtuoso' },
  { type: 'ESTP', name: 'The Entrepreneur' },
  { type: 'ENTP', name: 'The Debater' },
  { type: 'INFP', name: 'The Mediator' },
  { type: 'ENFP', name: 'The Campaigner' },
  { type: 'ISFP', name: 'The Adventurer' },
  { type: 'ESFP', name: 'The Entertainer' },
  { type: 'INFJ', name: 'The Advocate' },
  { type: 'ISFJ', name: 'The Protector' },
  { type: 'ENFJ', name: 'The Protagonist' },
  { type: 'ESFJ', name: 'The Consul' }
];

const layoutsDir = 'src/components/itinerary/layouts';

// Ensure directory exists
try {
  mkdirSync(layoutsDir, { recursive: true });
} catch (error) {
  // Directory might already exist
}

personalities.forEach(({ type, name }) => {
  const filename = `${type}Layout.vue`;
  const filepath = join(layoutsDir, filename);
  
  const content = `<template>
  <div class="${type.toLowerCase()}-layout">
    <h2>${type} - ${name}</h2>
    <p>Specialized travel planning layout for ${type} personality type.</p>
    <!-- TODO: Implement ${type}-specific layout -->
  </div>
</template>

<script setup lang="ts">
// Placeholder layout for ${type} personality
// This will be implemented in future tasks
</script>

<style scoped>
.${type.toLowerCase()}-layout {
  padding: 1rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}
</style>`;

  writeFileSync(filepath, content);
  console.log(`✅ Created ${filename}`);
});

console.log('🎉 All layout placeholder components created!');