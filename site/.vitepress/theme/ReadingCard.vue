<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useData } from 'vitepress';

const { page } = useData();
const enabled = ref(false);
const mounted = ref(false);
const settingsOpen = ref(false);
const opacity = ref(32);
const bandHeight = ref(29);
const palette = ref('rainbow');
const cardMode = ref<'blocks' | 'solid'>('blocks');
const solidColor = ref('sky');
const frame = reactive({ x: 0, y: 0, width: 640, height: 210 });
const moving = ref(false);
const viewportHeight = ref(0);
const adjustButton = ref<HTMLButtonElement>();
const settingsPanel = ref<HTMLElement>();
const menu = reactive({ x: 12, y: 84, width: 320 });
type Edge = 'n' | 'e' | 's' | 'w' | 'ne' | 'se' | 'sw' | 'nw';
const edges: { key: Edge; label: string }[] = [
  { key: 'n', label: '上边' }, { key: 'e', label: '右边' },
  { key: 's', label: '下边' }, { key: 'w', label: '左边' },
  { key: 'ne', label: '右上角' }, { key: 'se', label: '右下角' },
  { key: 'sw', label: '左下角' }, { key: 'nw', label: '左上角' }
];
const storageKey = 'agent-for-dummies:reading-card:v1';
const palettes = [
  { key: 'rainbow', name: '彩色', colors: ['#b5d962', '#c592cd', '#64c9da', '#e5b25b', '#ebd85c'] },
  { key: 'mint', name: '青绿', colors: ['#8acfc0', '#72bcd0', '#a8d791', '#b8e0cc', '#9dd2dd'] },
  { key: 'amber', name: '暖黄', colors: ['#e8ce70', '#e8b47a', '#d9c58e', '#efd994', '#dfbd69'] },
  { key: 'lavender', name: '淡紫', colors: ['#c3a4d7', '#aab2df', '#d4b4d2', '#b5c5e5', '#d5c3e7'] }
];
const colors = computed(() => palettes.find(item => item.key === palette.value)!.colors);
const solidColors = [
  { key: 'sky', name: '浅蓝', color: '#82c5df' },
  { key: 'sage', name: '浅绿', color: '#afd27f' },
  { key: 'amber', name: '暖黄', color: '#ead074' },
  { key: 'lavender', name: '淡紫', color: '#c5a4db' }
];
const tintStyle = computed(() => ({
  opacity: opacity.value / 100,
  backgroundColor: cardMode.value === 'solid' ? solidColors.find(item => item.key === solidColor.value)!.color : undefined
}));
const widths = [[14, 23, 21, 23, 19], [22, 19, 23, 17, 19], [11, 27, 18, 24, 20], [25, 16, 22, 21, 16]];
const rows = computed(() => Array.from({ length: Math.ceil(frame.height / bandHeight.value) }, (_, row) =>
  widths[row % widths.length].map((width, column) => ({ width, color: colors.value[(row * 2 + column) % colors.value.length] }))
));
const frameStyle = computed(() => ({ left: `${frame.x}px`, top: `${frame.y}px`, width: `${frame.width}px`, height: `${frame.height}px` }));
const settingsStyle = computed(() => ({ left: `${menu.x}px`, top: `${menu.y}px`, width: `${menu.width}px`, maxHeight: `${Math.max(80, viewportHeight.value - menu.y - 12)}px` }));
const sliderStyle = (value: number, min: number, max: number) => ({ '--range-progress': `${(value - min) / (max - min) * 100}%` });
let gesture: { id: number; mode: 'move' | Edge; x: number; y: number; frame: typeof frame } | null = null;
let placement = 0;

function topLimit() {
  const visibleBottom = (selector: string) => {
    const element = document.querySelector<HTMLElement>(selector);
    return element && element.getClientRects().length ? element.getBoundingClientRect().bottom : 0;
  };
  return Math.max(visibleBottom('.VPNav'), visibleBottom('.VPLocalNav'), 12) + 44;
}

function fitFrame() {
  viewportHeight.value = window.innerHeight;
  const top = topLimit();
  const maxWidth = Math.max(120, window.innerWidth - 16);
  const maxHeight = Math.max(60, window.innerHeight - top - 16);
  frame.width = Math.min(maxWidth, Math.max(Math.min(220, maxWidth), frame.width));
  frame.height = Math.min(maxHeight, Math.max(Math.min(86, maxHeight), frame.height));
  frame.x = Math.max(8, Math.min(frame.x, window.innerWidth - frame.width - 8));
  frame.y = Math.max(top, Math.min(frame.y, window.innerHeight - frame.height - 8));
  if (settingsOpen.value) positionSettings();
}

function positionSettings() {
  const anchor = adjustButton.value?.getBoundingClientRect();
  if (!anchor) return;
  viewportHeight.value = window.innerHeight;
  menu.width = Math.min(320, window.innerWidth - 24);
  menu.x = Math.max(12, Math.min(anchor.right - menu.width, window.innerWidth - menu.width - 12));
  menu.y = Math.min(Math.max(anchor.bottom + 10, document.querySelector('.VPNav')?.getBoundingClientRect().bottom || 0), Math.max(12, window.innerHeight - 100));
}

async function toggleSettings() {
  settingsOpen.value = !settingsOpen.value;
  if (settingsOpen.value) {
    positionSettings();
    await nextTick();
    settingsPanel.value?.querySelector<HTMLButtonElement>('button[aria-pressed="true"]')?.focus({ preventScroll: true });
  }
}

function dismissSettings(event: Event) {
  if (!settingsOpen.value) return;
  const target = event.target as Node | null;
  if (target && !settingsPanel.value?.contains(target) && !adjustButton.value?.contains(target)) settingsOpen.value = false;
}

async function placeOverText() {
  await nextTick();
  cancelAnimationFrame(placement);
  placement = requestAnimationFrame(() => {
    const documentBody = document.querySelector<HTMLElement>('.vp-doc');
    const bounds = documentBody?.getBoundingClientRect();
    const paragraph = [...documentBody?.querySelectorAll<HTMLElement>('p, li') || []].find(element => {
      const rect = element.getBoundingClientRect();
      return (element.textContent?.trim().length || 0) > 20 && rect.top >= topLimit() && rect.top < window.innerHeight - 100;
    });
    frame.width = Math.min(bounds?.width || 640, 760);
    frame.x = bounds?.left || (window.innerWidth - frame.width) / 2;
    frame.y = paragraph ? paragraph.getBoundingClientRect().top - 4 : Math.max(topLimit(), window.innerHeight * .35);
    fitFrame();
  });
}

function toggle() {
  enabled.value = !enabled.value;
  settingsOpen.value = false;
  if (enabled.value) void placeOverText();
}

function close() {
  enabled.value = false;
  settingsOpen.value = false;
  gesture = null;
  moving.value = false;
}

function startGesture(event: PointerEvent, mode: 'move' | Edge) {
  if (event.button !== 0) return;
  event.preventDefault();
  gesture = { id: event.pointerId, mode, x: event.clientX, y: event.clientY, frame: { ...frame } };
  moving.value = true;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function updateGesture(event: PointerEvent) {
  if (!gesture || gesture.id !== event.pointerId) return;
  const dx = event.clientX - gesture.x;
  const dy = event.clientY - gesture.y;
  if (gesture.mode === 'move') {
    frame.x = gesture.frame.x + dx;
    frame.y = gesture.frame.y + dy;
  } else {
    resizeFromEdge(gesture.mode, dx, dy, gesture.frame);
  }
  if (gesture.mode === 'move') fitFrame();
}

function resizeFromEdge(edge: Edge, dx: number, dy: number, origin = { ...frame }) {
  const minWidth = Math.min(220, window.innerWidth - 16);
  const minHeight = Math.min(86, window.innerHeight - topLimit() - 16);
  const right = origin.x + origin.width;
  const bottom = origin.y + origin.height;
  if (edge.includes('w')) {
    frame.x = Math.max(8, Math.min(origin.x + dx, right - minWidth));
    frame.width = right - frame.x;
  } else if (edge.includes('e')) {
    frame.width = Math.max(minWidth, Math.min(origin.width + dx, window.innerWidth - origin.x - 8));
  }
  if (edge.includes('n')) {
    frame.y = Math.max(topLimit(), Math.min(origin.y + dy, bottom - minHeight));
    frame.height = bottom - frame.y;
  } else if (edge.includes('s')) {
    frame.height = Math.max(minHeight, Math.min(origin.height + dy, window.innerHeight - origin.y - 8));
  }
}

function endGesture() {
  gesture = null;
  moving.value = false;
}

function keyboardMove(event: KeyboardEvent, edge?: Edge) {
  const directions: Record<string, [number, number]> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  const direction = directions[event.key];
  if (!direction) return;
  event.preventDefault();
  const step = event.shiftKey ? 40 : 10;
  if (edge) {
    resizeFromEdge(edge, direction[0] * step, direction[1] * step);
  } else {
    frame.x += direction[0] * step;
    frame.y += direction[1] * step;
  }
  fitFrame();
}

function escape(event: KeyboardEvent) {
  if (event.key !== 'Escape' || !enabled.value || document.querySelector('dialog[open]')) return;
  if (settingsOpen.value) {
    settingsOpen.value = false;
    adjustButton.value?.focus({ preventScroll: true });
  }
  else close();
}

function save() {
  if (!mounted.value) return;
  document.documentElement.classList.toggle('reading-card-active', enabled.value);
  try {
    localStorage.setItem(storageKey, JSON.stringify({ enabled: enabled.value, opacity: opacity.value, bandHeight: bandHeight.value, palette: palette.value, mode: cardMode.value, solidColor: solidColor.value, height: frame.height }));
  } catch { /* Reading still works when browser storage is unavailable. */ }
}

watch([enabled, opacity, bandHeight, palette, cardMode, solidColor, () => frame.height], save);
watch(() => page.value.relativePath, () => { settingsOpen.value = false; if (enabled.value) void placeOverText(); });
onMounted(() => {
  mounted.value = true;
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    if (typeof saved.enabled === 'boolean') enabled.value = saved.enabled;
    if (Number.isFinite(saved.opacity)) opacity.value = Math.max(12, Math.min(55, saved.opacity));
    if (Number.isFinite(saved.bandHeight)) bandHeight.value = Math.max(20, Math.min(52, saved.bandHeight));
    if (palettes.some(item => item.key === saved.palette)) palette.value = saved.palette;
    if (saved.mode === 'solid' || saved.mode === 'blocks') cardMode.value = saved.mode;
    if (solidColors.some(item => item.key === saved.solidColor)) solidColor.value = saved.solidColor;
    if (Number.isFinite(saved.height)) frame.height = Math.max(86, Math.min(600, saved.height));
  } catch { /* Ignore incomplete or old preferences. */ }
  save();
  if (enabled.value) void placeOverText();
  window.addEventListener('resize', fitFrame);
  window.addEventListener('keydown', escape);
  document.addEventListener('pointerdown', dismissSettings, true);
  document.addEventListener('focusin', dismissSettings);
});
onUnmounted(() => {
  cancelAnimationFrame(placement);
  window.removeEventListener('resize', fitFrame);
  window.removeEventListener('keydown', escape);
  document.removeEventListener('pointerdown', dismissSettings, true);
  document.removeEventListener('focusin', dismissSettings);
  document.documentElement.classList.remove('reading-card-active');
});
</script>

<template>
  <div class="reading-card-navigation">
    <div v-if="enabled" class="reading-card-navigation-tools" role="group" aria-label="阅读模式设置">
      <button ref="adjustButton" type="button" class="reading-card-nav-tool" :class="{ 'is-open': settingsOpen }" :aria-expanded="settingsOpen" aria-controls="reading-card-settings" aria-label="调整阅读卡" title="调整配色与透明度" @click="toggleSettings">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-linecap="round" aria-hidden="true"><path d="M2 4h12M2 12h12"/><circle cx="6" cy="4" r="2" fill="var(--vp-c-bg)"/><circle cx="10" cy="12" r="2" fill="var(--vp-c-bg)"/></svg>
        <span>调整</span>
      </button>
      <button type="button" class="reading-card-nav-tool" aria-label="将阅读卡重新放到正文" title="阅读卡归位" @click="placeOverText">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-linecap="round" aria-hidden="true"><path d="M5 2H2v3M11 2h3v3M2 11v3h3M14 11v3h-3"/><rect x="5" y="5" width="6" height="6" rx="1"/></svg>
        <span>归位</span>
      </button>
    </div>
  <button class="reading-card-toggle" :class="{ 'is-active': enabled }" type="button" :aria-pressed="enabled" aria-label="ADHD 阅读模式" title="开启或关闭彩色阅读卡" @click="toggle">
    <svg width="20" height="18" viewBox="0 0 20 18" fill="none" aria-hidden="true">
      <rect x="1" y="2" width="18" height="14" rx="3" stroke="currentColor" />
      <path d="M3 5h5v3H3z" fill="#9dcc63" /><path d="M8 5h9v3H8z" fill="#9fc2e5" />
      <path d="M3 10h8v3H3z" fill="#d6b1de" /><path d="M11 10h6v3h-6z" fill="#e8c86e" />
    </svg>
    <span>ADHD 阅读</span>
  </button>
  </div>
  <Teleport v-if="mounted" to="body">
    <div v-if="enabled && settingsOpen" id="reading-card-settings" ref="settingsPanel" class="reading-card-settings" :style="settingsStyle" role="region" aria-label="阅读卡设置">
      <fieldset class="reading-card-modes">
        <legend>卡片模式</legend>
        <div>
          <button type="button" :class="{ selected: cardMode === 'blocks' }" :aria-pressed="cardMode === 'blocks'" @click="cardMode = 'blocks'">色块模式</button>
          <button type="button" :class="{ selected: cardMode === 'solid' }" :aria-pressed="cardMode === 'solid'" @click="cardMode = 'solid'">纯色模式</button>
        </div>
      </fieldset>
      <fieldset v-if="cardMode === 'blocks'" class="reading-card-palettes">
        <legend>颜色</legend>
        <button v-for="item in palettes" :key="item.key" type="button" :class="{ selected: palette === item.key }" :aria-pressed="palette === item.key" @click="palette = item.key">
          <span class="reading-card-swatch" :style="{ background: `linear-gradient(90deg, ${item.colors.map((color, i) => `${color} ${i * 20}% ${(i + 1) * 20}%`).join(', ')})` }" aria-hidden="true" />
          {{ item.name }}
        </button>
      </fieldset>
      <fieldset v-else class="reading-card-palettes">
        <legend>颜色</legend>
        <button v-for="item in solidColors" :key="item.key" type="button" :class="{ selected: solidColor === item.key }" :aria-pressed="solidColor === item.key" @click="solidColor = item.key">
          <span class="reading-card-swatch" :style="{ backgroundColor: item.color }" aria-hidden="true" />
          {{ item.name }}
        </button>
      </fieldset>
      <label class="reading-card-slider">颜色浓度 <input v-model.number="opacity" type="range" min="12" max="55" :style="sliderStyle(opacity, 12, 55)" aria-label="颜色浓度" /><output>{{ opacity }}%</output></label>
      <label v-if="cardMode === 'blocks'" class="reading-card-slider">色带高度 <input v-model.number="bandHeight" type="range" min="20" max="52" :style="sliderStyle(bandHeight, 20, 52)" aria-label="色带高度" /><output>{{ bandHeight }}px</output></label>
      <p>右上角手柄移动，拖动四边或四角调整大小。</p>
    </div>
    <div v-if="enabled" class="reading-card" :class="{ 'is-moving': moving }" :style="frameStyle" role="region" aria-label="彩色阅读卡">
      <div class="reading-card-tint" :style="tintStyle" aria-hidden="true">
        <template v-if="cardMode === 'blocks'">
        <div v-for="(row, index) in rows" :key="index" class="reading-card-band" :style="{ height: `${bandHeight}px` }">
          <span v-for="(tile, column) in row" :key="column" :style="{ flex: tile.width, backgroundColor: tile.color }" />
        </div>
        </template>
      </div>
        <button type="button" class="reading-card-grip" aria-label="拖动阅读卡，或用方向键移动" title="拖动移动，也可用方向键移动" @pointerdown="startGesture($event, 'move')" @pointermove="updateGesture" @pointerup="endGesture" @pointercancel="endGesture" @lostpointercapture="endGesture" @keydown="keyboardMove">
          <svg width="14" height="16" viewBox="0 0 14 16" fill="currentColor" aria-hidden="true"><circle cx="4" cy="4" r="1.2"/><circle cx="10" cy="4" r="1.2"/><circle cx="4" cy="8" r="1.2"/><circle cx="10" cy="8" r="1.2"/><circle cx="4" cy="12" r="1.2"/><circle cx="10" cy="12" r="1.2"/></svg>
        </button>
      <button v-for="edge in edges" :key="edge.key" type="button" class="reading-card-edge" :class="`reading-card-edge-${edge.key}`" :tabindex="edge.key === 'se' ? 0 : -1" :aria-label="`从${edge.label}调整阅读卡大小`" :title="`拖动${edge.label}调整大小`" @pointerdown="startGesture($event, edge.key)" @pointermove="updateGesture" @pointerup="endGesture" @pointercancel="endGesture" @lostpointercapture="endGesture" @keydown="keyboardMove($event, edge.key)" />
    </div>
  </Teleport>
</template>

<style scoped>
.reading-card-navigation, .reading-card-navigation-tools { display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0; }
.reading-card-navigation { margin-right: 16px; gap: 8px; }
.reading-card-nav-tool { display: inline-flex; align-items: center; gap: 5px; height: 34px; padding: 0 8px; border-radius: 7px; color: var(--vp-c-text-2); font: 500 12px/1.6 var(--vp-font-family-base); }
.reading-card-nav-tool:hover, .reading-card-nav-tool.is-open { color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); }
.reading-card-toggle { display: inline-flex; align-items: center; gap: 7px; flex-shrink: 0; padding: 8px 11px; border: 1px solid var(--vp-c-divider); border-radius: 8px; color: var(--vp-c-text-2); background: var(--vp-c-bg); font: 500 12px/1.6 var(--vp-font-family-base); cursor: pointer; }
.reading-card-toggle:hover, .reading-card-toggle.is-active { color: var(--vp-c-brand-1); border-color: var(--vp-c-brand-2); background: var(--vp-c-bg-soft); }
.reading-card { position: fixed; z-index: 29; border: 1px solid rgb(89 125 137 / 28%); border-radius: 10px; pointer-events: none; }
.reading-card-tint { position: absolute; inset: 0; overflow: hidden; border-radius: 9px; mix-blend-mode: multiply; }
.reading-card-band { display: flex; gap: 3px; padding-bottom: 3px; }
.reading-card-band span { min-width: 0; }
.reading-card-grip { position: absolute; z-index: 2; right: -1px; top: -36px; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; padding: 0; border: 1px solid var(--vp-c-border); border-radius: 8px; background: var(--vp-c-bg-elv); color: var(--vp-c-text-2); box-shadow: 0 2px 8px rgb(27 66 88 / 5%); cursor: grab; touch-action: none; user-select: none; pointer-events: auto; }
.reading-card-grip:hover { color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); }
.is-moving .reading-card-grip { cursor: grabbing; }
.reading-card-grip:active, .reading-card-edge:active { transform: none; }
.reading-card-edge { position: absolute; z-index: 1; padding: 0; border: 0; background: transparent; pointer-events: auto; touch-action: none; }
.reading-card-edge-n, .reading-card-edge-s { left: 10px; right: 10px; height: 12px; cursor: ns-resize; }
.reading-card-edge-n { top: -6px; }
.reading-card-edge-s { bottom: -6px; }
.reading-card-edge-e, .reading-card-edge-w { top: 10px; bottom: 10px; width: 12px; cursor: ew-resize; }
.reading-card-edge-e { right: -6px; }
.reading-card-edge-w { left: -6px; }
.reading-card-edge-ne, .reading-card-edge-se, .reading-card-edge-sw, .reading-card-edge-nw { width: 18px; height: 18px; }
.reading-card-edge-ne, .reading-card-edge-nw { top: -7px; }
.reading-card-edge-se, .reading-card-edge-sw { bottom: -7px; }
.reading-card-edge-ne, .reading-card-edge-se { right: -7px; }
.reading-card-edge-nw, .reading-card-edge-sw { left: -7px; }
.reading-card-edge-ne, .reading-card-edge-sw { cursor: nesw-resize; }
.reading-card-edge-nw, .reading-card-edge-se { cursor: nwse-resize; }
.reading-card:has(.reading-card-edge:hover), .reading-card.is-moving { border-color: var(--vp-c-brand-2); }
.reading-card-settings { position: fixed; z-index: 60; overflow-y: auto; padding: 17px; border: 1px solid var(--vp-c-border); border-radius: 11px; background: var(--vp-c-bg-elv); color: var(--vp-c-text-1); box-shadow: 0 6px 24px rgb(27 66 88 / 9%); font: 12px/1.7 var(--vp-font-family-base); }
.reading-card-modes { padding: 0; margin: 0 0 14px; border: 0; }
.reading-card-modes legend { margin-bottom: 8px; font-weight: 500; }
.reading-card-modes > div { display: flex; gap: 3px; padding: 3px; border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg-soft); }
.reading-card-modes button { flex: 1; padding: 5px 8px; border: 1px solid transparent; border-radius: 5px; color: var(--vp-c-text-2); }
.reading-card-modes button.selected { color: var(--vp-c-brand-1); border-color: var(--vp-c-border); background: var(--vp-c-bg-elv); }
.reading-card-palettes { border: 0; padding: 0; margin: 0 0 13px; }
.reading-card-palettes legend { margin-bottom: 8px; font-weight: 500; }
.reading-card-palettes button { width: 25%; padding: 4px; border-radius: 6px; color: var(--vp-c-text-2); }
.reading-card-palettes button.selected { color: var(--vp-c-brand-1); background: var(--vp-c-bg-soft); }
.reading-card-swatch { display: block; height: 12px; margin-bottom: 4px; border-radius: 3px; opacity: .75; }
.reading-card-slider { display: flex; align-items: center; gap: 10px; margin-top: 8px; white-space: nowrap; }
.reading-card-slider input { --range-fill: color-mix(in srgb, var(--vp-c-brand-2) 25%, var(--vp-c-bg-soft)); --range-track: var(--vp-c-divider); --range-thumb-border: color-mix(in srgb, var(--vp-c-brand-1) 45%, var(--vp-c-border)); appearance: none; -webkit-appearance: none; width: 100%; min-width: 40px; height: 26px; padding: 0; border: 0; background: transparent; cursor: pointer; }
.reading-card-slider input::-webkit-slider-runnable-track { height: 4px; border: 0; border-radius: 99px; background: linear-gradient(to right, var(--range-fill) 0 var(--range-progress), var(--range-track) var(--range-progress) 100%); }
.reading-card-slider input::-webkit-slider-thumb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; margin-top: -5px; border: 1.5px solid var(--range-thumb-border); border-radius: 50%; background: var(--vp-c-bg-elv); box-shadow: 0 1px 3px rgb(27 66 88 / 12%); }
.reading-card-slider input::-moz-range-track { height: 4px; border: 0; border-radius: 99px; background: var(--range-track); }
.reading-card-slider input::-moz-range-progress { height: 4px; border-radius: 99px; background: var(--range-fill); }
.reading-card-slider input::-moz-range-thumb { width: 12px; height: 12px; border: 1.5px solid var(--range-thumb-border); border-radius: 50%; background: var(--vp-c-bg-elv); box-shadow: 0 1px 3px rgb(27 66 88 / 12%); }
.reading-card-slider output { width: 42px; flex-shrink: 0; text-align: right; font-variant-numeric: tabular-nums; color: var(--vp-c-text-2); }
.reading-card-settings p { margin: 11px 0 0; color: var(--vp-c-text-3); font-size: 11px; }
.reading-card-toggle:focus-visible, .reading-card-nav-tool:focus-visible, .reading-card button:focus-visible, .reading-card-settings button:focus-visible, .reading-card-settings input:focus-visible { outline: 2px solid var(--vp-c-brand-2); outline-offset: 3px; }
:global(.dark) .reading-card-tint { mix-blend-mode: screen; }
:global(.reading-card-active .pointer-sparkle), :global(.reading-card-active .tap-wave) { display: none; }
@media (max-width: 1100px) {
  .reading-card-toggle span, .reading-card-nav-tool span { display: none; }
  .reading-card-navigation, .reading-card-navigation-tools { gap: 3px; }
  .reading-card-navigation { margin-right: 8px; margin-left: 6px; }
  .reading-card-toggle { width: 32px; height: 34px; padding: 0; justify-content: center; }
  .reading-card-nav-tool { width: 28px; padding: 0; justify-content: center; }
}
@media (max-width: 639px) { :global(.reading-card-active .VPNavBarTitle .title) { font-size: 0; } }
@media (pointer: coarse) {
  .reading-card-edge-n, .reading-card-edge-s { height: 18px; }
  .reading-card-edge-n { top: -9px; }
  .reading-card-edge-s { bottom: -9px; }
  .reading-card-edge-e, .reading-card-edge-w { width: 18px; }
  .reading-card-edge-e { right: -9px; }
  .reading-card-edge-w { left: -9px; }
  .reading-card-edge-ne, .reading-card-edge-se, .reading-card-edge-sw, .reading-card-edge-nw { width: 26px; height: 26px; }
  .reading-card-edge-ne, .reading-card-edge-nw { top: -11px; }
  .reading-card-edge-se, .reading-card-edge-sw { bottom: -11px; }
  .reading-card-edge-ne, .reading-card-edge-se { right: -11px; }
  .reading-card-edge-nw, .reading-card-edge-sw { left: -11px; }
}
</style>
