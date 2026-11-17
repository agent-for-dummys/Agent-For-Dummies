<script setup lang="ts">
import {ref} from 'vue';

const props = defineProps<{axis: 'x' | 'y'; label: string}>();
const emit = defineEmits<{start: []; drag: [distance: number]; step: [direction: number]}>();
const origin = ref<{pointer: number; position: number}>();
const position = (event: PointerEvent) => props.axis === 'x' ? event.clientX : -event.clientY;

function start(event: PointerEvent) {
  if (event.button !== 0 || origin.value) return;
  origin.value = {pointer: event.pointerId, position: position(event)};
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  emit('start');
}

function move(event: PointerEvent) {
  if (origin.value?.pointer === event.pointerId) emit('drag', position(event) - origin.value.position);
}

function end(event: PointerEvent) {
  if (origin.value?.pointer === event.pointerId) origin.value = undefined;
}

function key(event: KeyboardEvent) {
  const keys = props.axis === 'x' ? ['ArrowLeft', 'ArrowRight'] : ['ArrowDown', 'ArrowUp'];
  const direction = keys.indexOf(event.key);
  if (direction < 0) return;
  event.preventDefault();
  emit('step', direction ? 1 : -1);
}
</script>

<template>
  <div :class="axis === 'x' ? 'column-divider' : 'output-divider'" role="separator"
    :aria-label="label" :aria-orientation="axis === 'x' ? 'vertical' : 'horizontal'" tabindex="0"
    @pointerdown="start" @pointermove="move" @pointerup="end" @pointercancel="end" @lostpointercapture="end" @keydown="key">
    <i/>
  </div>
</template>

<style scoped>
.column-divider,.output-divider{display:flex;align-items:center;justify-content:center;touch-action:none}
.column-divider{cursor:col-resize}.column-divider i{height:36px;width:2px}
.output-divider{height:8px;flex:none;cursor:row-resize}.output-divider i{width:32px;height:2px}
.column-divider i,.output-divider i{background:var(--vp-c-border);border-radius:2px}
@media(max-width:600px){.column-divider{display:none}}
</style>
