import { ref, onMounted, onBeforeUnmount } from 'vue'

// چرخش خودکار دسته‌ها + هاور دستی
export function useCategoryCycle(ids) {
  const active = ref(null)
  let idx = 0
  let timer, restartTimer, startTimer
  let reduce = false

  function step() {
    active.value = ids[idx++ % ids.length]
  }
  function cycle() {
    clearInterval(timer)
    if (reduce) return
    step()
    timer = setInterval(step, 2600)
  }
  function hold(id) {
    clearInterval(timer)
    clearTimeout(restartTimer)
    active.value = id
  }
  function release() {
    active.value = null
    clearTimeout(restartTimer)
    restartTimer = setTimeout(cycle, 1800)
  }

  onMounted(() => {
    reduce = matchMedia('(prefers-reduced-motion:reduce)').matches
    startTimer = setTimeout(cycle, 2200)
  })
  onBeforeUnmount(() => {
    clearInterval(timer)
    clearTimeout(restartTimer)
    clearTimeout(startTimer)
  })

  return { active, hold, release }
}