<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { VERT, FRAG } from '../../shaders/nova.js'

const canvas = ref(null)
let cleanup = () => {}

onMounted(() => {
  const el = canvas.value
  const gl = el && el.getContext('webgl', { antialias: false })
  if (!gl) return

  function compile(t, src) {
    const sh = gl.createShader(t)
    gl.shaderSource(sh, src)
    gl.compileShader(sh)
    return sh
  }
  const prog = gl.createProgram()
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT))
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG))
  gl.linkProgram(prog)
  gl.useProgram(prog)
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
  const loc = gl.getAttribLocation(prog, 'a_position')
  gl.enableVertexAttribArray(loc)
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

  const U = (n) => gl.getUniformLocation(prog, n)
  const uRes = U('u_res'), uTime = U('u_time'), uMouse = U('u_mouse'), uPresence = U('u_presence')
  /* NOVA palette: Midnight #060E26, Deep #0C193C, Royal #1D356B, Electric #2D57A1 */
  gl.uniform3fv(
    U('u_colors'),
    new Float32Array([0.024, 0.055, 0.149, 0.047, 0.098, 0.235, 0.114, 0.208, 0.42, 0.176, 0.341, 0.631])
  )

  let tx = 0, ty = 0, tp = 0, mx = 0, my = 0, pr = 0, last = null, raf = 0
  const t0 = performance.now()
  const reduce = matchMedia('(prefers-reduced-motion:reduce)').matches

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2)
    const rw = Math.max(1, Math.round(el.clientWidth * dpr))
    const rh = Math.max(1, Math.round(el.clientHeight * dpr))
    const k = Math.min(1, Math.sqrt(2000000 / (rw * rh)))
    const w = Math.max(1, Math.round(rw * k))
    const h = Math.max(1, Math.round(rh * k))
    if (el.width !== w || el.height !== h) {
      el.width = w
      el.height = h
      gl.viewport(0, 0, w, h)
    }
  }

  function draw(now) {
    const dt = last === null ? 0 : Math.min((now - last) / 1000, 0.1)
    last = now
    const f = 1 - Math.exp(-12 * dt)
    mx += (tx - mx) * f
    my += (ty - my) * f
    pr += (tp - pr) * f
    resize()
    gl.uniform2f(uRes, el.width, el.height)
    gl.uniform1f(uTime, ((now - t0) / 1000) * 0.575)
    gl.uniform2f(uMouse, mx, my)
    gl.uniform1f(uPresence, pr)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
  }
  function loop(now) {
    draw(now)
    raf = requestAnimationFrame(loop)
  }

  const onMove = (e) => {
    const r = el.getBoundingClientRect()
    tx = ((e.clientX - r.left) / r.width) * 2 - 1
    ty = -(((e.clientY - r.top) / r.height) * 2 - 1)
    if (tp === 0 && pr < 0.01) {
      mx = tx
      my = ty
    }
    tp = 1
  }
  const onLeave = () => (tp = 0)
  const onResize = () => {
    resize()
    if (reduce) draw(performance.now())
  }
  const onVisibility = () => {
    if (reduce) return
    if (document.visibilityState === 'visible') {
      last = null
      raf = requestAnimationFrame(loop)
    } else {
      cancelAnimationFrame(raf)
    }
  }

  addEventListener('pointermove', onMove, { passive: true })
  document.documentElement.addEventListener('pointerleave', onLeave)
  addEventListener('blur', onLeave)
  addEventListener('resize', onResize)
  document.addEventListener('visibilitychange', onVisibility)

  if (reduce) draw(performance.now())
  else raf = requestAnimationFrame(loop)

  cleanup = () => {
    cancelAnimationFrame(raf)
    removeEventListener('pointermove', onMove)
    document.documentElement.removeEventListener('pointerleave', onLeave)
    removeEventListener('blur', onLeave)
    removeEventListener('resize', onResize)
    document.removeEventListener('visibilitychange', onVisibility)
  }
})

onBeforeUnmount(() => cleanup())
</script>

<template>
  <canvas id="bg" ref="canvas" aria-hidden="true"></canvas>
</template>