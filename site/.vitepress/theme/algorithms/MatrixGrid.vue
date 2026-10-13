<script setup lang="ts">
import { format } from './toy-attention';
const props = withDefaults(defineProps<{
  matrix: number[][]; x: number; y: number; name: string; cell?: number;
  focusRow?: number; focusCol?: number; operand?: [number, number];
  hidden?: string[]; mutedColumns?: number[]; tone?: string; showDimensions?: boolean;
}>(), { cell: 44, hidden: () => [], mutedColumns: () => [], tone: 'neutral', showDimensions: false });
const key = (row: number, col: number) => `${row}-${col}`;
</script>

<template>
  <g class="matrix-grid" :data-matrix="name">
    <text :x="x + matrix[0].length * cell / 2" :y="y - 19" class="matrix-name">{{ name }}</text>
    <path :d="`M${x - 4} ${y - 3}h-7v${matrix.length * cell + 2}h7 M${x + matrix[0].length * cell} ${y - 3}h7v${matrix.length * cell + 2}h-7`" class="matrix-bracket" />
    <g v-for="(row, ri) in matrix" :key="ri"><g v-for="(value, ci) in row" :key="ci" :data-cell="key(ri, ci)">
      <rect :x="x + ci * cell" :y="y + ri * cell" :width="cell - 4" :height="cell - 4" rx="5" class="matrix-cell" :class="[tone, { focus: focusRow === ri || focusCol === ci, operand: operand?.[0] === ri && operand?.[1] === ci, muted: mutedColumns.includes(ci) }]" />
      <text :x="x + ci * cell + (cell - 4) / 2" :y="y + ri * cell + (cell - 4) / 2 + 4" class="matrix-value" :class="{ muted: mutedColumns.includes(ci) }">{{ hidden.includes(key(ri, ci)) ? '·' : format(value) }}</text>
    </g></g>
    <text v-if="showDimensions" :x="x + matrix[0].length * cell / 2" :y="y + matrix.length * cell + 18" class="matrix-dim">{{ matrix.length }} × {{ matrix[0].length }}</text>
  </g>
</template>

<style scoped>
.matrix-name { fill: var(--vp-c-text-1); text-anchor: middle; font: 14px var(--vp-font-family-mono); }
.matrix-cell { --tile: var(--algo-neutral); fill: color-mix(in srgb, var(--tile) 16%, var(--vp-c-bg)); stroke: color-mix(in srgb, var(--tile) 65%, var(--vp-c-bg)); stroke-width: 1; transition: fill .2s, stroke .2s; }
.matrix-cell.query { --tile: var(--algo-query); } .matrix-cell.key { --tile: var(--algo-key); } .matrix-cell.value { --tile: var(--algo-value); } .matrix-cell.green { --tile: var(--algo-output); }
.matrix-cell.focus { fill: color-mix(in srgb, var(--tile) 28%, var(--vp-c-bg)); stroke: var(--tile); }
.matrix-cell.operand { fill: color-mix(in srgb, var(--tile) 40%, var(--vp-c-bg)); stroke: var(--vp-c-brand-1); stroke-width: 1.8; }
.matrix-value { fill: var(--vp-c-text-1); text-anchor: middle; font: 13px var(--vp-font-family-mono); }
.matrix-dim { fill: var(--vp-c-text-2); text-anchor: middle; font: 11px var(--vp-font-family-mono); }
.matrix-bracket { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.2; }
.muted { opacity: .5; }
@media (prefers-reduced-motion: reduce) { .matrix-cell { transition: none; } }
</style>
