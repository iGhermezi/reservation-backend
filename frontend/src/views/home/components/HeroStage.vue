<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { categories, HUB, STAGE_ORDER, pinImage } from '../data/categories'

const props = defineProps({
  active: { type: String, default: null },
})
defineEmits(['hold', 'release'])

const routesEl = ref(null)
const sparksEl = ref(null)

// آیتم‌ها به ترتیب نمایش
const items = STAGE_ORDER.map((id) => categories.find((c) => c.id === id))

// مسیر منحنی از مرکز تا هر دسته (به ترتیب categories)
const routes = computed(() =>
  categories.map((it) => {
    const ey = it.y + (it.y < 30 ? 12 : it.y > 70 ? -4 : 6)
    const mx = (HUB.x + it.x) / 2 + (it.x < HUB.x ? -6 : 6)
    const my = (HUB.y + ey) / 2 + (it.y < HUB.y ? -6 : 6)
    return { id: it.id, d: `M${HUB.x} ${HUB.y} Q${mx} ${my} ${it.x} ${ey}` }
  })
)

let raf = 0

onMounted(() => {
  if (matchMedia('(prefers-reduced-motion:reduce)').matches) return

  const paths = [...routesEl.value.querySelectorAll('path.route')]
  const sparkEls = [...sparksEl.value.children]
  const S = paths.map((p, i) => ({
    p,
    el: sparkEls[i],
    len: p.getTotalLength(),
    dur: 4200 + i * 650,
    off: i * 0.17,
    rev: i % 2 === 1,
    id: p.dataset.id,
  }))

  function frame(now) {
    S.forEach((o) => {
      const t = (now / o.dur + o.off) % 1
      const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2
      const fade = Math.sin(Math.PI * t)
      const hot = props.active === o.id
      const heads = o.el.children
      for (let k = 0; k < 4; k++) {
        const tt = Math.max(0, e - k * 0.028)
        const u = o.rev ? 1 - tt : tt
        const pt = o.p.getPointAtLength(u * o.len)
        heads[k].style.left = pt.x + '%'
        heads[k].style.top = pt.y + '%'
      }
      o.el.style.opacity = (hot ? 1 : 0.8) * fade
    })
    raf = requestAnimationFrame(frame)
  }
  raf = requestAnimationFrame(frame)
})

onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <section class="stage">
    <svg ref="routesEl" class="routes" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs>
        <linearGradient id="ar" x1="0" x2="1">
          <stop offset="0" stop-color="#4b8bff" stop-opacity="0" />
          <stop offset=".5" stop-color="#8fbcff" />
          <stop offset="1" stop-color="#4b8bff" stop-opacity=".2" />
        </linearGradient>
      </defs>
      <ellipse class="arc" cx="52" cy="58" rx="60" ry="38" stroke="url(#ar)" transform="rotate(-6 52 58)" />
      <ellipse class="arc" cx="60" cy="40" rx="44" ry="26" stroke="url(#ar)" style="opacity: 0.5" transform="rotate(-10 60 40)" />

      <template v-for="r in routes" :key="'ribbon-' + r.id">
        <path class="ribbon" style="stroke-width: 40; stroke: rgba(30, 60, 150, 0.22)" :d="r.d" />
        <path class="ribbon" :d="r.d" />
      </template>
      <path
        v-for="r in routes"
        :key="'route-' + r.id"
        class="route"
        :class="{ on: active === r.id }"
        :data-id="r.id"
        :d="r.d"
      />
    </svg>

    <!-- نور متحرک روی مسیرها -->
    <div ref="sparksEl" class="sparks">
      <div v-for="r in routes" :key="'spark-' + r.id" class="spark">
        <i></i><i></i><i></i><i></i>
      </div>
    </div>

    <template v-for="(it, i) in items" :key="it.id">
      <div v-if="it.id === 'beauty'" class="it pin" style="left: 52.5%; top: 49%; width: 25%">
        <div class="in" style="--d: 0.9s">
          <img :src="pinImage" alt="" style="display: block; width: 100%" />
        </div>
      </div>

      <div class="it" :style="{ left: it.x + '%', top: it.y + '%', width: it.w + '%' }">
        <div class="in" :style="{ '--d': 0.15 + i * 0.17 + 's' }">
          <div class="fl" :style="{ '--d2': -i * 1.1 + 's' }">
            <div class="lift" :class="{ on: active === it.id }">
              <div class="gw"></div>
              <img :src="it.img" :alt="it.name" />
              <div class="tg">{{ it.name.toUpperCase() }}</div>
              <div
                class="hit"
                tabindex="0"
                role="button"
                :aria-label="it.name"
                @mouseenter="$emit('hold', it.id)"
                @focus="$emit('hold', it.id)"
                @click="$emit('hold', it.id)"
                @mouseleave="$emit('release')"
                @blur="$emit('release')"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>