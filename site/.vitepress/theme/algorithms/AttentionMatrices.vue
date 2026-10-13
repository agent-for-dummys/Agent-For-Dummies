<script setup lang="ts">
import { computed, ref } from 'vue';
import MatrixGrid from './MatrixGrid.vue';
import { useFrames } from './useFrames';
import { attention, inputs, tokens, format } from './toy-attention';
const props = defineProps<{ step: number; queryIndex: number; revision: number; reducedMotion: boolean; speed: number; active: boolean; paused: boolean }>();
const role = ref<'Q' | 'K' | 'V'>('Q');
const transpose = (m: number[][]) => m[0].map((_, i) => m.map(row => row[i]));
const all = [0, 1, 2].map(i => attention(i));
const x = transpose(inputs), q = transpose(all[0].queries), k = transpose(all[0].keys), v = transpose(all[0].values);
const scores = [0, 1, 2].map(key => all.map(a => a.scores[key]));
const scaled = scores.map(row => row.map(score => score / Math.sqrt(2)));
const weights = [0, 1, 2].map(key => all.map(a => a.weights[key]));
const output = transpose(all.map(a => a.output));
const multiplication = computed(() => {
  if (props.step === 1) return { left: role.value === 'V' ? [[1, 1], [0, 1]] : [[1, 0], [0, 1]], right: x, result: role.value === 'Q' ? q : role.value === 'K' ? k : v, names: [`W${role.value.toLowerCase()}`, 'X', role.value], tones: ['neutral', 'neutral', role.value === 'Q' ? 'query' : role.value === 'K' ? 'key' : 'value'] };
  if (props.step === 2) return { left: transpose(k), right: q, result: scores, names: ['Kᵀ', 'Q', 'S'], tones: ['key', 'query', 'neutral'] };
  return { left: v, right: weights, result: output, names: ['V', 'A', 'B'], tones: ['value', 'neutral', 'green'] };
});
const isProduct = computed(() => [1, 2, 5].includes(props.step));
const terms = computed(() => multiplication.value.left[0].length);
const total = computed(() => isProduct.value ? multiplication.value.left.length * terms.value : 3);
const { frame, complete } = useFrames({ count: () => total.value, reset: () => [props.step, props.queryIndex, props.revision, role.value], active: () => props.active, paused: () => props.paused, reducedMotion: () => props.reducedMotion, speed: () => props.speed });
const row = computed(() => isProduct.value ? Math.min(multiplication.value.left.length - 1, Math.floor(frame.value / terms.value)) : Math.min(2, frame.value));
const term = computed(() => complete.value ? terms.value - 1 : frame.value % terms.value);
const mutedColumns = computed(() => [0, 1, 2].filter(i => i !== props.queryIndex));
const hidden = computed(() => multiplication.value.result.map((_, ri) => `${ri}-${props.queryIndex}`).filter((_, ri) => !complete.value && ri >= Math.floor((frame.value + 1) / terms.value)));
const arithmetic = computed(() => {
  const m = multiplication.value;
  const end = complete.value ? terms.value : term.value + 1;
  const values = m.left[row.value].slice(0, end);
  const sum = values.reduce((s, value, i) => s + value * m.right[i][props.queryIndex], 0);
  return `${m.names[2]}[${row.value + 1},${props.queryIndex + 1}] = ` + values.map((value, i) => `${format(value)} × ${format(m.right[i][props.queryIndex])}`).join(' + ') + ` = ${format(sum)}`;
});
const matrixY = (matrix: number[][]) => 106 - matrix.length * 22;
</script>

<template>
  <div class="attention-matrices" :data-frame="frame" :data-complete="complete">
    <div v-if="step === 1" class="projection-picker" role="group" aria-label="选择投影矩阵"><button v-for="item in (['Q', 'K', 'V'] as const)" :key="item" type="button" :aria-pressed="role === item" :class="[{ active: role === item }, item.toLowerCase()]" @click="role = item">{{ item }}</button></div>
    <div class="matrix-canvas" tabindex="0" aria-label="注意力矩阵图，可横向滚动查看">
      <svg class="matrix-svg" viewBox="0 0 720 225" role="img" :aria-label="`注意力第 ${step + 1} 步矩阵计算`">
        <template v-if="step === 0">
          <MatrixGrid :matrix="x" :x="300" :y="79" name="X" :focus-col="queryIndex" :muted-columns="mutedColumns" :show-dimensions="true" />
          <g v-for="(word, i) in tokens" :key="word"><text :x="320 + i * 44" y="32" class="word" :class="{ chosen: i === queryIndex }">{{ word }}</text><path :d="`M${320 + i * 44} 41v10`" class="input-line" /></g>
          <text x="246" y="105" class="dimension">特征 1</text><text x="246" y="149" class="dimension">特征 2</text>
        </template>
        <template v-else-if="isProduct">
          <MatrixGrid :matrix="multiplication.result" :x="62" :y="matrixY(multiplication.result)" :name="multiplication.names[2]" :tone="multiplication.tones[2]" :focus-col="queryIndex" :operand="[row, queryIndex]" :hidden="hidden" :muted-columns="mutedColumns" />
          <text x="227" y="113" class="operator">=</text>
          <MatrixGrid :matrix="multiplication.left" :x="304" :y="matrixY(multiplication.left)" :name="multiplication.names[0]" :tone="multiplication.tones[0]" :focus-row="row" :operand="[row, term]" />
          <text x="478" y="113" class="operator">×</text>
          <MatrixGrid :matrix="multiplication.right" :x="546" :y="matrixY(multiplication.right)" :name="multiplication.names[1]" :tone="multiplication.tones[1]" :focus-col="queryIndex" :operand="[term, queryIndex]" :muted-columns="mutedColumns" />
          <text x="360" y="210" class="arithmetic">{{ arithmetic }}</text>
        </template>
        <template v-else>
          <MatrixGrid :matrix="step === 3 ? scaled : weights" :x="119" :y="54" :name="step === 3 ? 'S / √2' : 'A'" :focus-col="queryIndex" :operand="[row, queryIndex]" :muted-columns="mutedColumns" />
          <path d="M453 110H282" class="transform-arrow"/><path d="M293 103L282 110L293 117" class="transform-arrow"/><text x="367" y="94" class="operation">{{ step === 3 ? '÷ √2' : 'softmax' }}</text>
          <MatrixGrid :matrix="step === 3 ? scores : scaled" :x="500" :y="54" :name="step === 3 ? 'S' : 'S / √2'" :focus-col="queryIndex" :operand="[row, queryIndex]" :muted-columns="mutedColumns" />
          <text x="360" y="210" class="arithmetic">{{ step === 3 ? `${format(scores[row][queryIndex])} / √2 = ${format(scaled[row][queryIndex])}` : `A[${row + 1},${queryIndex + 1}] = exp(${format(scaled[row][queryIndex])}) / Σ exp(本列) = ${format(weights[row][queryIndex])}` }}</text>
        </template>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.projection-picker { display: flex; gap: 5px; margin: 0 0 2px; }
.projection-picker button { padding: 2px 9px; border-radius: 3px; font: 12px var(--vp-font-family-mono); color: var(--vp-c-text-2); }
.projection-picker .active.q { background: color-mix(in srgb, var(--algo-query) 25%, var(--vp-c-bg)); } .projection-picker .active.k { background: color-mix(in srgb, var(--algo-key) 25%, var(--vp-c-bg)); } .projection-picker .active.v { background: color-mix(in srgb, var(--algo-value) 25%, var(--vp-c-bg)); }
.matrix-canvas { overflow-x: auto; overscroll-behavior-x: contain; }
.matrix-svg { display: block; width: 100%; height: 200px; min-width: 590px; color: var(--vp-c-text-1); font-family: var(--vp-font-family-base); }
.word, .dimension, .operator, .arithmetic, .operation { fill: currentColor; text-anchor: middle; }
.word { font-size: 12px; fill: var(--vp-c-text-3); } .word.chosen { fill: var(--vp-c-text-1); font-weight: 600; }
.dimension { font-size: 11px; fill: var(--vp-c-text-3); }
.operator { font-size: 25px; font-family: Georgia, serif; }
.arithmetic { font: 12px var(--vp-font-family-mono); }
.operation { font: italic 16px Georgia, serif; }
.transform-arrow { fill: none; stroke: var(--vp-c-text-1); stroke-width: 2; }
.input-line { fill: none; stroke: var(--vp-c-divider); }
</style>
