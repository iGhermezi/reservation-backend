<script setup>
defineProps({
  categories: { type: Array, required: true },
  active: { type: String, default: null },
})
defineEmits(['hold', 'release'])
</script>

<template>
  <div class="cats">
    <button
      v-for="c in categories"
      :key="c.id"
      class="cat"
      :class="{ on: active === c.id }"
      @mouseenter="$emit('hold', c.id)"
      @focus="$emit('hold', c.id)"
      @click="$emit('hold', c.id)"
      @mouseleave="$emit('release')"
      @blur="$emit('release')"
    >
      <svg viewBox="0 0 24 24" v-html="c.icon"></svg>
      <span>{{ c.name }}</span>
    </button>
  </div>
</template>