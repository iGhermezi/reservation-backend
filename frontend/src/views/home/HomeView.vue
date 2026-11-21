<script setup>
import ShaderBackground from '../../components/layout/ShaderBackground.vue'
import NavBar from '../../components/layout/NavBar.vue'
import HeroIntro from './components/HeroIntro.vue'
import CategoryTabs from './components/CategoryTabs.vue'
import HeroStage from './components/HeroStage.vue'
import { categories } from './data/categories'
import { useCategoryCycle } from './composables/useCategoryCycle'

const { active, hold, release } = useCategoryCycle(categories.map((c) => c.id))
</script>

<template>
  <ShaderBackground />
  <NavBar />
  <main class="hero">
    <HeroIntro>
      <CategoryTabs :categories="categories" :active="active" @hold="hold" @release="release" />
    </HeroIntro>
    <HeroStage :active="active" @hold="hold" @release="release" />
  </main>
</template>