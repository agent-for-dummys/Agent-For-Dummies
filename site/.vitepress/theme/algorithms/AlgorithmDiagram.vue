<script setup lang="ts">
import { computed, useId } from 'vue';
import { attention, multiHead, inputs, tokens, format, vectorText, type WalkthroughKind } from './toy-attention';
const props = defineProps<{ kind: WalkthroughKind; step: number; queryIndex: number; revision: number; reducedMotion: boolean; active: boolean; paused: boolean; speed: number }>();
const uid = useId().replace(/:/g, '');
const a = computed(() => attention(props.queryIndex, props.kind === 'mask'));
const heads = computed(() => multiHead(props.queryIndex));
const cols = [180, 380, 580], superscript = ['¹', '²', '³'];
const marker = `url(#${uid}-arrow)`;
const animated = computed(() => props.active && !props.paused && !props.reducedMotion);
const encoder = [
  { y: 34, label: 'Embedding + 位置', stages: [0] },
  { y: 79, label: 'Self-Attention', stages: [1] },
  { y: 124, label: 'Add & Norm', stages: [2] },
  { y: 169, label: 'FFN → Add & Norm', stages: [3] }
];
const decoder = [
  { y: 34, label: 'Embedding + 位置', stages: [4] },
  { y: 79, label: 'Masked Attention → Add & Norm', stages: [4] },
  { y: 124, label: 'Cross-Attention → Add & Norm', stages: [5] },
  { y: 169, label: 'FFN → Add & Norm', stages: [6] },
  { y: 214, label: 'Linear → Softmax', stages: [7] }
];
</script>

<template>
  <div class="algorithm-canvas" tabindex="0" aria-label="算法图，可横向滚动查看">
    <svg :key="revision" class="algorithm-svg" :class="{ architecture: kind === 'transformer' }" :viewBox="kind === 'transformer' ? '0 0 720 285' : '0 0 720 250'" role="img" :aria-label="`${kind} 第 ${step + 1} 步过程图`">
      <defs><marker :id="`${uid}-arrow`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" markerUnits="userSpaceOnUse" orient="auto"><path d="M0 0L10 5L0 10z" class="arrow-tip" /></marker></defs>
      <template v-if="kind === 'attention'">
        <template v-if="step < 2">
          <g v-for="(x, i) in cols" :key="i">
            <text :x="x" :y="step === 0 ? 38 : 20" class="label">{{ tokens[i] }}</text>
            <rect :x="x - 22" :y="step === 0 ? 58 : 32" width="44" :height="step === 0 ? 88 : 40" class="node neutral" :class="{ selected: i === queryIndex }"/>
            <text :x="x" :y="step === 0 ? 88 : 58" class="number">{{ step === 0 ? inputs[i][0] : vectorText(inputs[i]) }}</text><text v-if="step === 0" :x="x" y="126" class="number">{{ inputs[i][1] }}</text>
            <text v-if="step === 0" :x="x" y="170" class="math">a{{ superscript[i] }}</text>
            <g v-else v-for="(role, ri) in ['Q', 'K', 'V']" :key="role">
              <path :id="`${uid}-projection-${i}-${ri}`" :d="`M${x} 72L${x + (ri - 1) * 53} 120`" class="flow" :marker-end="marker"/>
              <circle v-if="animated" r="3" class="dot"><animateMotion :dur="`${1.5 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-projection-${i}-${ri}`"/></animateMotion></circle>
              <rect :x="x + (ri - 1) * 53 - 20" y="125" width="40" height="64" class="node" :class="['query', 'key', 'value'][ri]"/>
              <text :x="x + (ri - 1) * 53" y="150" class="math">{{ role.toLowerCase() }}{{ superscript[i] }}</text><text :x="x + (ri - 1) * 53" y="174" class="small-number">{{ vectorText((ri === 0 ? a.queries : ri === 1 ? a.keys : a.values)[i]) }}</text>
            </g>
          </g>
        </template>
        <template v-else-if="step < 5">
          <rect x="28" y="143" width="58" height="60" class="node query selected"/><text x="57" y="168" class="math">q{{ superscript[queryIndex] }}</text><text x="57" y="189" class="small-number">{{ vectorText(a.query) }}</text>
          <g v-for="(x, i) in cols" :key="i">
            <path :id="`${uid}-match-${i}`" :d="`M57 143Q57 105 ${x} 80`" class="ink-flow" :marker-end="marker"/>
            <path :d="`M${x} 143V83`" class="ink-flow" :marker-end="marker"/>
            <circle :cx="x" cy="75" r="5" class="match-dot"/><text :x="x" y="53" class="score">{{ step === 4 ? `${(a.weights[i] * 100).toFixed(1)}%` : format((step === 2 ? a.scores : a.scaled)[i]) }}</text>
            <rect :x="x - 24" y="143" width="48" height="60" class="node key"/><text :x="x" y="168" class="math">k{{ superscript[i] }}</text><text :x="x" y="189" class="small-number">{{ vectorText(a.keys[i]) }}</text>
            <circle v-if="animated" r="3" class="dot"><animateMotion :dur="`${1.8 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-match-${i}`"/></animateMotion></circle>
          </g>
        </template>
        <template v-else>
          <rect x="27" y="14" width="67" height="39" class="node output"/><text x="60" y="40" class="math">b{{ superscript[queryIndex] }}</text><text x="80" y="74" class="number">{{ vectorText(a.output) }}</text>
          <rect x="27" y="183" width="46" height="43" class="node query selected"/><text x="50" y="211" class="math">q{{ superscript[queryIndex] }}</text>
          <path d="M638 33H99" class="sum-flow" :marker-end="marker"/>
          <g v-for="(x, i) in [160, 360, 560]" :key="i">
            <path :d="`M50 183L${x} 121M${x} 183V121`" class="ink-flow"/>
            <circle :cx="x" cy="116" r="5" class="match-dot"/><text :x="x" y="96" class="number">{{ format(a.weights[i]) }}</text>
            <path :d="`M${x + 7} 116H${x + 48}M${x + 60} 183V132`" class="sum-flow" :marker-end="marker"/>
            <rect :x="x + 48" y="104" width="24" height="24" class="multiply"/><text :x="x + 60" y="123" class="operator">×</text>
            <path :id="`${uid}-sum-${i}`" :d="`M${x + 60} 104V33H99`" class="sum-flow" :marker-end="marker"/>
            <rect :x="x - 18" y="183" width="36" height="43" class="node key"/><text :x="x" y="211" class="math">k{{ superscript[i] }}</text>
            <rect :x="x + 42" y="183" width="36" height="43" class="node value"/><text :x="x + 60" y="211" class="math">v{{ superscript[i] }}</text>
            <circle v-if="animated" r="3" class="sum-dot"><animateMotion :dur="`${2 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-sum-${i}`"/></animateMotion></circle>
          </g>
        </template>
      </template>

      <template v-else-if="kind === 'multi-head'">
        <rect x="14" y="100" width="74" height="46" class="node neutral"/><text x="51" y="120" class="label">{{ tokens[queryIndex] }}</text><text x="51" y="138" class="small-number">{{ vectorText(inputs[queryIndex]) }}</text>
        <g v-for="(head, i) in [heads.first, heads.second]" :key="i">
          <path :id="`${uid}-head-${i}`" :d="`M88 123H105V${i ? 178 : 68}H150`" class="flow" :marker-end="marker"/>
          <text x="203" :y="i ? 144 : 34" class="label">Head {{ i + 1 }}</text>
          <g v-for="(role, ri) in ['Q', 'K', 'V']" :key="role"><rect :x="154 + ri * 35" :y="i ? 156 : 46" width="28" height="45" class="node" :class="['query', 'key', 'value'][ri]" :style="{ opacity: step === 0 ? 1 : .65 }"/><text :x="168 + ri * 35" :y="i ? 184 : 74" class="math small">{{ role }}</text></g>
          <path :d="`M255 ${i ? 178 : 68}H289`" class="flow" :marker-end="marker"/>
          <rect x="296" :y="i ? 156 : 46" width="137" height="45" class="node output" :class="{ selected: step === 1, quiet: step < 1 }"/><text x="365" :y="i ? 184 : 74" class="number">{{ step >= 1 ? vectorText(head.output) : 'Attention' }}</text>
          <text v-if="step === 1" x="310" :y="i ? 218 : 108" class="small-number">α = {{ vectorText(head.weights) }}</text>
          <path :d="`M433 ${i ? 178 : 68}H453V123H479`" class="flow" :class="{ muted: step < 2 }" :marker-end="marker"/>
          <circle v-if="animated" r="3" class="dot"><animateMotion :dur="`${1.7 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-head-${i}`"/></animateMotion></circle>
        </g>
        <text x="520" y="55" class="label">Concat</text><rect x="483" y="65" width="74" height="115" class="node neutral" :class="{ selected: step === 2, quiet: step < 2 }"/><text v-for="(value, i) in heads.concatenated" :key="i" x="520" :y="88 + i * 26" class="number">{{ step >= 2 ? format(value) : '·' }}</text>
        <path d="M558 123H617" class="flow" :class="{ muted: step < 3 }" :marker-end="marker"/><text x="588" y="110" class="math small">Wᴼ</text>
        <rect x="624" y="84" width="74" height="77" class="node output" :class="{ selected: step === 3, quiet: step < 3 }"/><text v-for="(value, i) in heads.output" :key="i" x="661" :y="111 + i * 29" class="number">{{ step >= 3 ? format(value) : '·' }}</text>
      </template>

      <template v-else-if="kind === 'transformer'">
        <text x="181" y="17" class="lane">Encoder · 我 / 喜欢 / 你</text><text x="539" y="17" class="lane">Decoder · BOS</text>
        <g v-for="(block, i) in encoder" :key="`e${i}`">
          <path v-if="i" :id="`${uid}-encoder-${i}`" :d="`M181 ${block.y - 17}V${block.y - 4}`" class="flow" :class="{ muted: step < block.stages[0] }" :marker-end="marker"/>
          <rect x="56" :y="block.y" width="250" height="28" rx="4" class="node value" :class="{ selected: block.stages.includes(step), quiet: step < block.stages[0] }"/><text x="181" :y="block.y + 19" class="label">{{ block.label }}</text>
          <circle v-if="i && animated && block.stages.includes(step)" r="3" class="dot"><animateMotion :dur="`${1.5 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-encoder-${i}`"/></animateMotion></circle>
        </g>
        <path d="M181 197V220" class="flow" :class="{ muted: step < 3 }" :marker-end="marker"/><rect x="108" y="225" width="147" height="28" rx="4" class="node output" :class="{ quiet: step < 3 }"/><text x="181" y="244" class="label">最终输出 Z</text>
        <path :id="`${uid}-cross`" d="M255 239H330V138H409" class="flow" :class="{ muted: step < 5 }" :marker-end="marker"/><text x="352" y="205" class="math small">K,V</text><text v-if="step === 5" x="568" y="118" class="math small">Q ↓</text>
        <circle v-if="step === 5 && animated" r="3.5" class="dot"><animateMotion :dur="`${2 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-cross`"/></animateMotion></circle>
        <g v-for="(block, i) in decoder" :key="`d${i}`">
          <path v-if="i" :id="`${uid}-decoder-${i}`" :d="`M539 ${block.y - 17}V${block.y - 4}`" class="flow" :class="{ muted: step < block.stages[0] }" :marker-end="marker"/>
          <rect x="414" :y="block.y" width="250" height="28" rx="4" class="node query" :class="{ selected: block.stages.includes(step), quiet: step < block.stages[0] }"/><text x="539" :y="block.y + 19" class="label">{{ block.label }}</text>
          <circle v-if="i && animated && block.stages.includes(step)" r="3" class="dot"><animateMotion :dur="`${1.5 / speed}s`" repeatCount="1" fill="freeze"><mpath :href="`#${uid}-decoder-${i}`"/></animateMotion></circle>
        </g>
        <text x="181" y="279" class="dimension">完整层堆叠 N 次</text>
        <g v-if="step === 7"><path d="M539 242V258" class="flow" :marker-end="marker"/><text x="539" y="280" class="math">I</text></g>
      </template>

    </svg>
  </div>
</template>

<style scoped>
.algorithm-canvas { overflow-x: auto; overscroll-behavior-x: contain; }
.algorithm-svg { display: block; width: 100%; height: 220px; min-width: 590px; color: var(--vp-c-text-1); font-family: var(--vp-font-family-base); }
.algorithm-svg.architecture { height: 250px; }
.node { --tile: var(--algo-neutral); fill: color-mix(in srgb, var(--tile) 18%, var(--vp-c-bg)); stroke: color-mix(in srgb, var(--tile) 60%, var(--vp-c-bg)); stroke-width: 1.3; }
.query { --tile: var(--algo-query); } .key { --tile: var(--algo-key); } .value { --tile: var(--algo-value); } .output { --tile: var(--algo-output); }
.selected { fill: color-mix(in srgb, var(--tile) 29%, var(--vp-c-bg)); stroke: var(--vp-c-brand-1); stroke-width: 1.8; }
.quiet { fill: var(--vp-c-bg-alt); stroke: var(--vp-c-divider); color: var(--vp-c-text-3); opacity: .65; }
.flow { fill: none; stroke: var(--vp-c-brand-2); stroke-width: 1.5; }
.ink-flow { fill: none; stroke: var(--vp-c-text-2); stroke-width: 1.3; }
.sum-flow { fill: none; stroke: var(--algo-output); stroke-width: 2; }
.multiply { fill: var(--vp-c-bg-soft); stroke: var(--vp-c-text-3); }
.muted { opacity: .25; } .blocked { stroke: var(--vp-c-text-3); opacity: .3; stroke-dasharray: 4 5; } .append-flow { stroke-dasharray: 5 4; }
.arrow-tip, .dot { fill: var(--vp-c-brand-2); } .sum-dot { fill: var(--algo-output); } .match-dot { fill: var(--vp-c-text-1); }
.label, .number, .small-number, .math, .operator, .score, .lane, .dimension { fill: currentColor; text-anchor: middle; }
.label { font-size: 14px; } .number { font: 14px var(--vp-font-family-mono); } .small-number { font: 10px var(--vp-font-family-mono); }
.math { font: italic 22px Georgia, serif; } .math.small { font-size: 15px; } .operator { font: 24px Georgia, serif; }
.score { font: 18px var(--vp-font-family-mono); } .lane { font-size: 12px; font-weight: 600; } .dimension { font-size: 11px; fill: var(--vp-c-text-2); } .dim { fill: var(--vp-c-text-3); }
.arrival { animation: arrival .5s ease-out; }
@keyframes arrival { from { opacity: .2; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { .arrival { animation: none; } }
</style>
