<script setup lang="ts">
import { computed, useId } from 'vue';
import { tokens } from './toy-attention';
const props = defineProps<{ queryIndex: number }>();
const emit = defineEmits<{ select: [index: number] }>();
const uid = useId().replace(/:/g, '');
const columns = [170, 360, 550], superscript = ['¹', '²', '³'];
const target = computed(() => columns[props.queryIndex]);
const branch = (i: number) => i === props.queryIndex ? `M${columns[i]} 216V98` : `M${columns[i]} 216V170C${columns[i]} 135 ${(columns[i] + target.value) / 2} 134 ${target.value - 5} 95`;
</script>

<template>
  <div class="masked-canvas" tabindex="0" aria-label="三个输入和三个输出各自对齐；高亮当前输出的可见连接，未来输入由挡板截住" :data-query="queryIndex">
    <svg class="masked-svg" viewBox="0 0 720 260" role="img" :aria-label="`${tokens[queryIndex]}对应的b${superscript[queryIndex]}读取前${queryIndex + 1}个输入，其余输入被遮住`">
      <defs>
        <pattern :id="`${uid}-hatch`" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 7L7 0" class="hatch-line"/></pattern>
        <marker :id="`${uid}-arrow`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" markerUnits="userSpaceOnUse" orient="auto"><path d="M0 0L10 5L0 10z" class="arrow-tip"/></marker>
      </defs>

      <g class="visible-routes">
        <g v-for="(x, i) in columns.slice(0, queryIndex + 1)" :key="i" :data-source="i" class="allowed-connection">
          <path :d="branch(i)" class="allowed-path"/>
        </g>
        <circle :cx="target" cy="92" r="5" class="junction"/>
        <path :d="`M${target} 87V60`" class="output-stem" :marker-end="`url(#${uid}-arrow)`"/>
      </g>

      <g v-for="(x, i) in columns" :key="`input-${i}`" :data-token="i" class="input-lane" :class="{ blocked: i > queryIndex }">
        <template v-if="i > queryIndex">
          <path :d="`M${x} 216V177`" class="blocked-path"/>
          <rect :x="x - 33" y="152" width="66" height="23" rx="4" class="mask-wall"/>
          <rect :x="x - 33" y="152" width="66" height="23" rx="4" :fill="`url(#${uid}-hatch)`"/>
          <text :x="x" y="168" class="gate-label">遮住</text>
        </template>
        <path v-else :d="`M${x - 25} 154h-5v19h5 M${x + 25} 154h5v19h-5`" class="open-gate"/>
        <g role="button" tabindex="0" :aria-label="`查看${tokens[i]}的计算`" :aria-pressed="i === queryIndex" class="input-position" @click="emit('select', i)" @keydown.enter="emit('select', i)" @keydown.space.prevent="emit('select', i)">
          <rect :x="x - 60" y="216" width="120" height="34" rx="6" class="input-node" :class="{ selected: i === queryIndex, masked: i > queryIndex }"/>
          <text :x="x" y="238" class="input-label" :class="{ dim: i > queryIndex }">{{ tokens[i] }}</text>
        </g>
      </g>

      <text x="79" y="43" class="row-label">输出</text>
      <g v-for="(x, i) in columns" :key="`output-${i}`" role="button" tabindex="0" :aria-label="`查看b${superscript[i]}的连接`" :aria-pressed="i === queryIndex" class="output-position" @click="emit('select', i)" @keydown.enter="emit('select', i)" @keydown.space.prevent="emit('select', i)">
        <rect :x="x - 60" y="17" width="120" height="39" rx="7" class="output-node" :class="{ selected: i === queryIndex }"/>
        <text :x="x" y="44" class="output-symbol" :class="{ dim: i !== queryIndex }">b{{ superscript[i] }}</text>
      </g>
      <text x="79" y="238" class="row-label">输入</text>
    </svg>
  </div>
</template>

<style scoped>
.masked-canvas { overflow-x: auto; overscroll-behavior-x: contain; }
.masked-svg { display: block; width: 100%; min-width: 590px; height: 220px; color: var(--vp-c-text-1); font-family: var(--vp-font-family-base); }
.allowed-path, .output-stem { fill: none; stroke: var(--algo-output); stroke-width: 2; stroke-linecap: round; }
.junction, .arrow-tip { fill: var(--algo-output); }
.blocked-path { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.4; stroke-dasharray: 3 5; opacity: .55; }
.mask-wall { fill: var(--vp-c-bg-alt); stroke: var(--algo-neutral); }
.hatch-line { stroke: var(--vp-c-divider); stroke-width: 1; }
.open-gate { fill: none; stroke: var(--algo-output); stroke-width: 1.4; opacity: .65; }
.input-node { fill: color-mix(in srgb, var(--algo-query) 7%, var(--vp-c-bg)); stroke: color-mix(in srgb, var(--algo-query) 65%, var(--vp-c-bg)); }
.input-node.selected { fill: color-mix(in srgb, var(--algo-query) 15%, var(--vp-c-bg)); stroke: var(--vp-c-brand-1); stroke-width: 1.5; }
.input-node.masked { fill: var(--vp-c-bg-alt); stroke: var(--vp-c-divider); }
.output-node { fill: var(--vp-c-bg); stroke: color-mix(in srgb, var(--algo-output) 55%, var(--vp-c-bg)); stroke-width: 1; }
.output-node.selected { fill: color-mix(in srgb, var(--algo-output) 14%, var(--vp-c-bg)); stroke: var(--vp-c-brand-1); stroke-width: 1.5; }
.row-label, .input-label, .gate-label, .output-symbol { fill: currentColor; text-anchor: middle; }
.row-label { fill: var(--vp-c-text-2); font-size: 12px; }
.input-label { font-size: 16px; } .gate-label { font-size: 12px; fill: var(--vp-c-text-2); } .output-symbol { font: italic 25px Georgia, serif; }
.dim { fill: var(--vp-c-text-3); }
.input-position, .output-position { cursor: pointer; } .input-position:focus-visible, .output-position:focus-visible { outline: none; } .input-position:focus-visible .input-node, .output-position:focus-visible .output-node { stroke: var(--vp-c-brand-1); stroke-width: 3; }
</style>
