<script setup lang="ts">
import { useId } from 'vue';
const props = defineProps<{ step: number; revision: number; reducedMotion: boolean; speed: number; active: boolean; paused: boolean }>();
const uid = useId().replace(/:/g, '');
const sentences = [['我', '喜欢', '机器', '学习'], ['我', '喜欢', 'NLP'], ['你好']];
const columns = [184, 317, 450, 583];
const delay = (row: number, col: number) => `${((row - 1) * .3 + (col - sentences[row].length) * .15) / props.speed}s`;
</script>

<template>
  <div class="padding-canvas" tabindex="0" aria-label="三个句子补齐为矩阵，并屏蔽 PAD 位置" :data-stage="step">
    <svg :key="`${step}-${revision}`" class="padding-svg" :class="{ paused: paused || !active }" viewBox="0 0 720 225" role="img" :aria-label="['三个句子的长度不同', '补齐 PAD，使三个句子都为四个位置', '只遮住 PAD，保留全部真实词'][step]" :style="{ '--fill-duration': `${450 / speed}ms` }">
      <defs><pattern :id="`${uid}-pad-hatch`" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 8L8 0" class="hatch-line"/></pattern></defs>
      <g v-for="(sentence, row) in sentences" :key="row" :data-row="row">
        <text x="68" :y="52 + row * 64" class="sentence-label">句子 {{ row + 1 }}</text>
        <g v-for="(x, col) in columns" :key="col" :data-col="col" :data-pad="col >= sentence.length">
          <template v-if="col < sentence.length">
            <rect :x="x - 53" :y="28 + row * 64" width="106" height="39" rx="6" class="word-cell"/>
            <text :x="x" :y="53 + row * 64" class="word">{{ sentence[col] }}</text>
          </template>
          <g v-else-if="step > 0" class="pad-cell" :class="{ arriving: step === 1 && !reducedMotion }" :style="{ animationDelay: delay(row, col) }">
            <rect :x="x - 53" :y="28 + row * 64" width="106" height="39" rx="6" class="pad-background"/>
            <text :x="x" :y="53 + row * 64" class="pad-word">&lt;PAD&gt;</text>
            <g v-if="step === 2" class="pad-cover" :class="{ closing: !reducedMotion }" :style="{ animationDelay: delay(row, col) }">
              <rect :x="x - 53" :y="28 + row * 64" width="106" height="39" rx="6" :fill="`url(#${uid}-pad-hatch)`" class="pad-mask"/>
              <path :d="`M${x - 53} ${row * 64 + 27}h106`" class="closed-edge"/>
            </g>
          </g>
        </g>
      </g>
      <text v-if="step > 0" x="386" y="215" class="matrix-shape">3 × 4</text>
    </svg>
  </div>
</template>

<style scoped>
.padding-canvas { overflow-x: auto; overscroll-behavior-x: contain; }
.padding-svg { display: block; width: 100%; min-width: 590px; height: 200px; color: var(--vp-c-text-1); font-family: var(--vp-font-family-base); }
.sentence-label, .word, .pad-word, .matrix-shape { fill: currentColor; text-anchor: middle; }
.sentence-label { font-size: 12px; fill: var(--vp-c-text-2); }
.word { font-size: 16px; } .pad-word { font: 14px var(--vp-font-family-mono); fill: var(--vp-c-text-3); }
.matrix-shape { font: 12px var(--vp-font-family-mono); fill: var(--vp-c-text-2); }
.word-cell { fill: color-mix(in srgb, var(--algo-query) 8%, var(--vp-c-bg)); stroke: color-mix(in srgb, var(--algo-query) 60%, var(--vp-c-bg)); }
.pad-background { fill: var(--vp-c-bg-alt); stroke: var(--vp-c-divider); }
.pad-mask { stroke: var(--algo-neutral); } .hatch-line { stroke: var(--algo-neutral); stroke-width: 1; opacity: .5; }
.closed-edge { fill: none; stroke: var(--algo-neutral); stroke-width: 2; }
.arriving { animation: fill-pad var(--fill-duration) ease-out both; }
.closing { transform-box: fill-box; transform-origin: top; animation: cover-pad var(--fill-duration) ease-out both; }
.paused .arriving, .paused .closing { animation-play-state: paused; }
@keyframes fill-pad { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes cover-pad { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@media (prefers-reduced-motion: reduce) { .arriving, .closing { animation: none; } }
</style>
