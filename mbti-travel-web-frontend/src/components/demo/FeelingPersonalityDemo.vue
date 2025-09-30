<template>
  <div class="feeling-personality-demo">
    <div class="demo-header">
      <h1>Feeling Personality Type Customizations Demo</h1>
      <p class="demo-description">
        Experience how the MBTI Travel Planner adapts to feeling-oriented personality types 
        (INFJ, ISFJ, ENFJ, ESFJ) with personalized features that emphasize emotional connection, 
        meaningful descriptions, group collaboration, and warm social experiences.
      </p>
    </div>

    <div class="personality-selector">
      <h2>Select Feeling Personality Type</h2>
      <div class="personality-buttons">
        <button
          v-for="personality in feelingPersonalities"
          :key="personality.type"
          :class="['personality-button', { active: selectedPersonality === personality.type }]"
          @click="selectedPersonality = personality.type"
        >
          <span class="personality-type">{{ personality.type }}</span>
          <span class="persona