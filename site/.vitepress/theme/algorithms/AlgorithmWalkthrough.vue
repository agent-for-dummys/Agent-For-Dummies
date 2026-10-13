<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useData } from 'vitepress';
import AlgorithmDiagram from './AlgorithmDiagram.vue';
import AttentionMatrices from './AttentionMatrices.vue';
import MaskedAttention from './MaskedAttention.vue';
import PaddingMask from './PaddingMask.vue';
import { tokens, walkthroughs, type WalkthroughKind } from './toy-attention';
const props = defineProps<{ kind: WalkthroughKind }>();
const lesson = computed(() => walkthroughs[props.kind]);
const step = ref(0), queryIndex = ref(0), revision = ref(0);
const playing = ref(false), paused = ref(false), inView = ref(false), reducedMotion = ref(false);
const speed = ref(1), view = ref<'vector' | 'matrix'>('matrix');
const root = ref<HTMLElement>();
const { page } = useData();
const current = computed(() => lesson.value.steps[step.value]);
const currentQuery = computed(() => props.kind === 'mask' ? step.value : queryIndex.value);
const canSelectQuery = computed(() => props.kind === 'attention' || props.kind === 'multi-head');
const first = computed(() => step.value === 0);
const last = computed(() => step.value === lesson.value.steps.length - 1);
let timer: ReturnType<typeof setTimeout> | undefined;
let observer: IntersectionObserver | undefined;
let motion: MediaQueryList | undefined;
function stop() { playing.value = false; clearTimeout(timer); }
function queue() {
  clearTimeout(timer);
  if (!playing.value) return;
  timer = setTimeout(() => {
    if (last.value) { stop(); return; }
    step.value++;
    revision.value++; queue();
  }, 5200 / speed.value);
}
function play() {
  if (playing.value) { stop(); paused.value = true; return; }
  if (last.value) step.value = 0;
  paused.value = false; playing.value = true; queue();
}
function go(index: number) { stop(); paused.value = false; step.value = Math.max(0, Math.min(index, lesson.value.steps.length - 1)); revision.value++; }
function next() { go(step.value + 1); }
function previous() { go(step.value - 1); }
function selectQuery(index: number) { stop(); paused.value = false; queryIndex.value = index; revision.value++; }
function setView(value: 'vector' | 'matrix') { stop(); paused.value = false; view.value = value; revision.value++; }
function replay() { paused.value = false; revision.value++; }
function keyboard(event: KeyboardEvent) {
  if (event.target !== event.currentTarget) return;
  if (event.key === 'ArrowRight') { event.preventDefault(); if (!last.value) next(); }
  if (event.key === 'ArrowLeft') { event.preventDefault(); if (!first.value) previous(); }
}
function visibility() { if (document.hidden) { stop(); paused.value = true; } }
function motionChange() { reducedMotion.value = motion?.matches || false; }
watch(speed, queue);
watch(() => page.value.relativePath, stop);
onMounted(async () => {
  motion = window.matchMedia('(prefers-reduced-motion: reduce)'); motionChange(); motion.addEventListener('change', motionChange);
  document.addEventListener('visibilitychange', visibility);
  await nextTick();
  observer = new IntersectionObserver(entries => {
    const visible = entries[0].isIntersecting;
    if (visible && !inView.value) revision.value++;
    inView.value = visible;
    if (!visible) stop();
  });
  if (root.value) observer.observe(root.value);
});
onUnmounted(() => { stop(); observer?.disconnect(); motion?.removeEventListener('change', motionChange); document.removeEventListener('visibilitychange', visibility); });
</script>

<template>
  <section ref="root" class="algorithm-walkthrough" :data-kind="kind" :data-step="step" :aria-label="lesson.title" tabindex="0" @keydown="keyboard">
    <nav v-if="kind !== 'mask'" class="algorithm-stages" aria-label="选择步骤"><button v-for="(item, i) in lesson.steps" :key="i" type="button" :class="{ active: step === i }" :aria-current="step === i ? 'step' : undefined" :aria-label="`第 ${i + 1} 步：${item.title}`" @click="go(i)">{{ item.title }}</button></nav>
    <div v-if="kind === 'attention' || canSelectQuery" class="algorithm-toolbar">
      <div v-if="kind === 'attention'" class="view-picker" role="group" aria-label="图解视图"><button type="button" :aria-pressed="view === 'vector'" :class="{ active: view === 'vector' }" @click="setView('vector')">关系图</button><button type="button" :aria-pressed="view === 'matrix'" :class="{ active: view === 'matrix' }" @click="setView('matrix')">矩阵</button></div>
      <div v-if="canSelectQuery" class="query-picker" role="group" aria-label="选择当前词"><span>{{ kind === 'mask' ? '当前词' : 'Query' }}</span><button v-for="(word, index) in tokens" :key="word" type="button" :aria-pressed="queryIndex === index" :class="{ active: queryIndex === index }" @click="selectQuery(index)">{{ word }}</button></div>
    </div>
    <div class="algorithm-body">
      <button type="button" class="algorithm-turn previous" :disabled="first" aria-label="上一步" @click="previous"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4L6 10L12 16"/></svg></button>
      <AttentionMatrices v-if="kind === 'attention' && view === 'matrix'" :step="step" :query-index="queryIndex" :revision="revision" :reduced-motion="reducedMotion" :speed="speed" :active="inView" :paused="paused" />
      <MaskedAttention v-else-if="kind === 'mask'" :query-index="currentQuery" @select="go" />
      <PaddingMask v-else-if="kind === 'padding'" :step="step" :revision="revision" :reduced-motion="reducedMotion" :active="inView" :paused="paused" :speed="speed" />
      <AlgorithmDiagram v-else :kind="kind" :step="step" :query-index="queryIndex" :revision="revision" :reduced-motion="reducedMotion" :active="inView" :paused="paused" :speed="speed" />
      <button type="button" class="algorithm-turn next" :disabled="last" aria-label="下一步" @click="next"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8 4L14 10L8 16"/></svg></button>
    </div>
    <p class="algorithm-note" aria-live="polite">{{ current.description }}</p>
    <footer class="algorithm-controls">
      <div class="algorithm-page-actions"><button type="button" class="play" :aria-label="kind === 'mask' ? playing ? '停止自动翻页' : '自动翻页' : playing ? '暂停播放' : '播放过程'" :aria-pressed="playing" @click="play">{{ playing ? 'Ⅱ 暂停' : kind === 'mask' ? '▶ 自动翻页' : '▶ 播放' }}</button></div>
      <div class="algorithm-secondary"><button v-if="kind !== 'mask'" type="button" class="replay-step" aria-label="重播本步动画" title="重播本步" @click="replay">↻</button><select v-model.number="speed" :aria-label="kind === 'mask' ? '翻页速度' : '播放速度'"><option :value=".5">0.5×</option><option :value="1">1×</option><option :value="1.5">1.5×</option></select></div>
    </footer>
  </section>
</template>

<style scoped>
.algorithm-walkthrough { --algo-query: #6a9ac4; --algo-key: #91a7bd; --algo-value: #68aaa7; --algo-output: #559b9b; --algo-neutral: #aebbc8; margin: 22px 0 28px; padding: 10px 18px 10px; border: 1px solid var(--vp-c-border); border-radius: 9px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.algorithm-body { position: relative; padding: 0 28px; }
.algorithm-turn { position: absolute; top: 50%; translate: 0 -50%; display: grid; place-items: center; width: 28px; height: 46px; border: 1px solid var(--vp-c-divider); border-radius: 7px; background: var(--vp-c-bg); color: var(--vp-c-text-2); }
.algorithm-turn.previous { left: -4px; } .algorithm-turn.next { right: -4px; }
.algorithm-turn svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.7; }
.algorithm-turn:hover:not(:disabled) { color: var(--vp-c-brand-1); border-color: var(--vp-c-brand-2); background: var(--vp-c-bg-soft); }
.algorithm-turn:disabled { opacity: .25; cursor: default; }
.algorithm-stages { display: flex; gap: 5px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 6px; border-bottom: 1px solid var(--vp-c-divider); scrollbar-width: thin; }
.algorithm-stages button { flex: 0 0 auto; padding: 4px 9px; border-radius: 4px; font-size: 12px; color: var(--vp-c-text-3); white-space: nowrap; }
.algorithm-stages button.active { color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); font-weight: 600; }
.algorithm-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 29px; margin-bottom: 4px; }
.view-picker, .query-picker { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.view-picker button, .query-picker button { padding: 3px 8px; border-radius: 4px; color: var(--vp-c-text-2); }
.view-picker button.active, .query-picker button.active { color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); }
.query-picker span { color: var(--vp-c-text-3); margin-right: 3px; font: 10px var(--vp-font-family-mono); }
.algorithm-walkthrough .algorithm-note { margin: 5px 0 7px; color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; }
.algorithm-controls, .algorithm-page-actions, .algorithm-secondary { display: flex; align-items: center; gap: 6px; }
.algorithm-controls { display: grid; grid-template-columns: 1fr auto 1fr; padding-top: 9px; border-top: 1px solid var(--vp-c-divider); }
.algorithm-page-actions { grid-column: 2; } .algorithm-secondary { justify-self: end; }
.algorithm-page-actions button { height: 28px; min-width: 29px; padding: 3px 8px; border: 1px solid var(--vp-c-border); border-radius: 5px; font-size: 12px; }
.algorithm-page-actions button.play { min-width: 67px; color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); }
.algorithm-page-actions button:disabled { opacity: .3; cursor: default; }
.replay-step { width: 26px; height: 26px; color: var(--vp-c-text-2); font-size: 18px; }
.algorithm-secondary select { padding: 3px 5px; border: 0; border-radius: 4px; background: var(--vp-c-bg); color: var(--vp-c-text-2); font: 11px var(--vp-font-family-mono); }
.algorithm-walkthrough:focus-visible, button:focus-visible, select:focus-visible { outline: 2px solid var(--vp-c-brand-2); outline-offset: 3px; }
@media (max-width: 639px) { .algorithm-walkthrough { padding: 11px 12px 10px; } .algorithm-stages button { padding: 4px 7px; font-size: 11px; } .algorithm-toolbar { gap: 5px; } .query-picker button { padding: 3px 6px; } .query-picker span { display: none; } }
</style>
