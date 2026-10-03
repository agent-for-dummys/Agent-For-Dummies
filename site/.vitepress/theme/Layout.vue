<script setup lang="ts">
import DefaultTheme from 'vitepress/theme';
import DocumentSearch from './DocumentSearch.vue';
import { useData } from 'vitepress';
import { nextTick, onMounted, onUnmounted, watch } from 'vue';

const { frontmatter, page } = useData();
let removeEffects = () => {};

onMounted(() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const waves = new Set<HTMLElement>();
  const stars = new Set<HTMLElement>();
  let lastSpawn = 0;
  let lastPoint: { x: number; y: number } | null = null;
  const clearStars = () => { stars.forEach(star => star.remove()); stars.clear(); lastPoint = null; };
  const placeEffect = (element: HTMLElement, x: number, y: number, target: EventTarget | null) => {
    const layer = target instanceof Element ? target.closest('dialog[open]')?.querySelector<HTMLElement>('.notebook-search-effects') : null;
    const box = layer?.getBoundingClientRect();
    if (box && (x < box.left || x > box.right || y < box.top || y > box.bottom)) return false;
    element.style.left = `${Math.min((box?.width || window.innerWidth) - 12, Math.max(12, x - (box?.left || 0)))}px`;
    element.style.top = `${Math.min((box?.height || window.innerHeight) - 12, Math.max(12, y - (box?.top || 0)))}px`;
    (layer || document.body).append(element);
    return true;
  };
  const sparkle = (x: number, y: number, burst = false, target: EventTarget | null = null) => {
    if (motion.matches || document.hidden || stars.size >= 20) return;
    const star = document.createElement('span');
    star.className = 'pointer-sparkle';
    star.setAttribute('aria-hidden', 'true');
    star.style.setProperty('--spark-size', `${burst ? 10 : 5 + Math.random() * 5}px`);
    star.style.setProperty('--spark-drift-x', `${(Math.random() - .5) * 15}px`);
    star.style.setProperty('--spark-drift-y', `${-8 - Math.random() * 9}px`);
    star.style.setProperty('--spark-turn', `${Math.random() * 60 - 30}deg`);
    if (!placeEffect(star, x, y, target)) return;
    stars.add(star);
    star.addEventListener('animationend', () => { stars.delete(star); star.remove(); }, { once: true });
  };
  const onMove = (event: PointerEvent) => {
    if (event.pointerType !== 'mouse' || !finePointer.matches || motion.matches) return;
    const now = performance.now();
    if (now - lastSpawn < 65 || (lastPoint && Math.hypot(event.clientX - lastPoint.x, event.clientY - lastPoint.y) < 7)) return;
    lastSpawn = now;
    lastPoint = { x: event.clientX, y: event.clientY };
    sparkle(event.clientX - 8, event.clientY + 9, false, event.target);
  };
  const onEnter = (event: PointerEvent) => {
    if (event.pointerType !== 'mouse' || !finePointer.matches || !(event.target instanceof Element)) return;
    const control = event.target.closest('a, button, summary, input[type="search"]');
    if (!control || (event.relatedTarget instanceof Node && control.contains(event.relatedTarget))) return;
    sparkle(event.clientX - 11, event.clientY - 7, true, event.target);
    sparkle(event.clientX + 10, event.clientY + 9, false, event.target);
  };
  const onVisibility = () => { if (document.hidden) clearStars(); };
  const onMotionChange = () => { if (motion.matches) { clearStars(); waves.forEach(wave => wave.remove()); waves.clear(); } };
  const onDialogClose = (event: Event) => {
    if (event.target instanceof HTMLDialogElement) { clearStars(); waves.forEach(wave => wave.remove()); waves.clear(); }
  };
  const onPointer = (event: PointerEvent) => {
    if (motion.matches || event.button !== 0 || !(event.target instanceof Element)) return;
    if (!event.target.closest('a, button, summary')) return;
    const wave = document.createElement('span');
    wave.className = 'tap-wave';
    wave.setAttribute('aria-hidden', 'true');
    if (!placeEffect(wave, event.clientX, event.clientY, event.target)) return;
    waves.add(wave);
    wave.addEventListener('animationend', () => { waves.delete(wave); wave.remove(); }, { once: true });
  };
  document.addEventListener('pointerdown', onPointer, { passive: true });
  document.addEventListener('pointermove', onMove, { passive: true });
  document.addEventListener('pointerover', onEnter, { passive: true });
  document.addEventListener('pointerleave', clearStars);
  document.addEventListener('visibilitychange', onVisibility);
  document.addEventListener('close', onDialogClose, true);
  motion.addEventListener('change', onMotionChange);
  const stop = watch(() => page.value.relativePath, async () => {
    clearStars();
    await nextTick();
    if (!motion.matches) document.querySelector('.VPDoc .content')?.animate(
      [{ opacity: .65, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 210, easing: 'ease-out' }
    );
  });
  removeEffects = () => {
    document.removeEventListener('pointerdown', onPointer);
    document.removeEventListener('pointermove', onMove);
    document.removeEventListener('pointerover', onEnter);
    document.removeEventListener('pointerleave', clearStars);
    document.removeEventListener('visibilitychange', onVisibility);
    document.removeEventListener('close', onDialogClose, true);
    motion.removeEventListener('change', onMotionChange);
    stop(); clearStars(); waves.forEach(wave => wave.remove());
  };
});
onUnmounted(() => removeEffects());
</script>

<template>
  <DefaultTheme.Layout>
    <template #nav-bar-content-before><DocumentSearch /></template>
    <template #doc-before>
      <div v-if="frontmatter.chapter" class="chapter-heading">
        <a :href="`${page.relativePath.startsWith('notes/') ? '../' : './'}catalog`">{{ frontmatter.category }}</a>
        <span class="chapter-divider">/</span>
        <span class="chapter-number">{{ frontmatter.chapter }}</span>
      </div>
    </template>
  </DefaultTheme.Layout>
</template>
