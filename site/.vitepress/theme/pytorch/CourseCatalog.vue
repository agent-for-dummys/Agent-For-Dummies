<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
import type {CourseSection, NavigationState, Track} from './course-navigation';

const props = defineProps<{sections: CourseSection[]; state: NavigationState; track: Track; navBottom: number}>();
const emit = defineEmits<{close: []; select: [id: string]}>();
const search = ref('');
const input = ref<HTMLInputElement>();
const panel = ref<HTMLElement>();
const expanded = ref<string[]>([]);
let previousFocus: HTMLElement | null = null;
const storageKey = `practice-catalog-${props.track}`;
const groups = computed(() => {
  const query = search.value.trim().toLocaleLowerCase();
  return props.sections.map(section => ({
    ...section,
    matches: section.items.filter(item => !query || `${section.title} ${item.title} ${item.search || ''}`.toLocaleLowerCase().includes(query)),
    count: section.tasks.filter(id => props.state.completed.includes(id)).length,
  })).filter(section => section.matches.length);
});
function toggle(id: string) {
  expanded.value = expanded.value.includes(id) ? expanded.value.filter(value => value !== id) : [...expanded.value, id];
  try { localStorage.setItem(storageKey, JSON.stringify(expanded.value)); } catch {}
}
function key(event: KeyboardEvent) {
  if (event.key === 'Escape') { event.preventDefault(); emit('close'); }
}
watch(() => props.state.selected, () => {
  const section = props.sections.find(section => section.items.some(item => item.id === props.state.selected));
  if (section && !expanded.value.includes(section.id)) expanded.value.push(section.id);
});
onMounted(async () => {
  previousFocus = document.activeElement as HTMLElement;
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (Array.isArray(saved)) expanded.value = saved.filter(id => props.sections.some(section => section.id === id));
  } catch {}
  const current = props.sections.find(section => section.items.some(item => item.id === props.state.selected)) || props.sections[0];
  if (current && !expanded.value.includes(current.id)) expanded.value.push(current.id);
  document.addEventListener('keydown', key);
  await nextTick();
  panel.value?.querySelector('.catalog-item.active')?.scrollIntoView({block: 'nearest'});
  input.value?.focus({preventScroll: true});
});
onUnmounted(() => {
  document.removeEventListener('keydown', key);
  if (document.activeElement === document.body) previousFocus?.focus({preventScroll: true});
});
</script>

<template>
  <div class="catalog-scrim" :style="{top: navBottom+'px'}" @click="emit('close')"/>
  <aside id="course-catalog" ref="panel" class="course-catalog" :style="{top: (navBottom+12)+'px'}" aria-labelledby="course-catalog-title">
    <header class="catalog-header">
      <h2 id="course-catalog-title">题目列表</h2>
      <button type="button" aria-label="收起题目列表" @click="emit('close')"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12 5-5 5 5 5"/></svg></button>
    </header>
    <label class="catalog-search">
      <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"/><path d="m13 13 4 4"/></svg>
      <input ref="input" v-model="search" type="search" aria-label="搜索题目或函数" placeholder="搜索题目或函数"/>
    </label>
    <div class="catalog-list">
      <section v-for="section in groups" :key="section.id" class="catalog-group">
        <button type="button" class="catalog-section" :aria-expanded="expanded.includes(section.id)||!!search.trim()" :aria-controls="'catalog-'+section.id" @click="toggle(section.id)">
          <svg class="section-chevron" :class="{expanded: expanded.includes(section.id)||search.trim()}" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 4 4 4-4 4"/></svg>
          <span>{{section.title}}</span><small>{{section.count}} / {{section.tasks.length}}</small>
        </button>
        <div v-if="expanded.includes(section.id)||search.trim()" :id="'catalog-'+section.id" class="catalog-items">
          <button v-for="item in section.matches" :key="item.id" type="button" class="catalog-item" :class="{active: state.selected===item.id}" :aria-current="state.selected===item.id?'page':undefined" @click="emit('select',item.id)">
            <svg v-if="item.learning" class="item-icon" viewBox="0 0 20 20" aria-hidden="true"><rect x="4" y="3" width="12" height="14" rx="2"/><path d="M7 3v14m3-10h3m-3 3h3"/></svg>
            <svg v-else class="item-icon" :class="{done: state.completed.includes(item.id)}" viewBox="0 0 20 20" aria-hidden="true"><path v-if="state.completed.includes(item.id)" d="m5 10 3 3 7-7"/><circle v-else cx="10" cy="10" r="3"/></svg>
            <span>{{item.title}}</span>
          </button>
        </div>
      </section>
      <p v-if="!groups.length" class="catalog-empty">没有找到匹配内容。</p>
    </div>
  </aside>
</template>

<style scoped>
.catalog-scrim{position:fixed;inset:64px 0 0;z-index:39;background:#18263312;backdrop-filter:blur(1px)}
.course-catalog{position:fixed;left:58px;bottom:14px;z-index:40;width:330px;max-width:calc(100vw - 72px);display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--vp-c-divider);border-radius:14px;background:var(--vp-c-bg);color:var(--vp-c-text-1);box-shadow:0 16px 50px -12px #18263328;font-family:var(--vp-font-family-base)}
.catalog-header{display:flex;align-items:center;justify-content:space-between;padding:20px 20px 15px;flex:none}
.catalog-header h2{margin:0;padding:0;border:0;font-size:15px;line-height:24px;font-weight:600;letter-spacing:.2px}
.catalog-header button{display:grid;place-items:center;width:26px;height:26px;border-radius:6px;color:var(--vp-c-text-3)}
.catalog-header button:hover{background:var(--vp-c-default-soft);color:var(--vp-c-text-1)}
svg{fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;flex:none;width:18px;height:18px}
.catalog-search{display:flex;align-items:center;gap:9px;margin:0 14px 13px;padding:9px 11px;background:var(--vp-c-bg-soft);border:1px solid transparent;border-radius:8px;color:var(--vp-c-text-3);flex:none}
.catalog-search:focus-within{border-color:#95cbe5}
.catalog-search input{min-width:0;width:100%;font-size:13px;line-height:20px;background:transparent;color:var(--vp-c-text-1);border:0;outline:none}
.catalog-search input::placeholder{color:var(--vp-c-text-3)}
.catalog-list{min-height:0;overflow:auto;padding:0 10px 20px;scrollbar-width:thin;scrollbar-color:#d0d3d6 transparent}
.catalog-group+.catalog-group{margin-top:7px}
.catalog-section{display:flex;align-items:center;gap:7px;width:100%;padding:10px 8px;text-align:left;font-size:12px;line-height:20px;font-weight:550;color:var(--vp-c-text-2);border-radius:6px}
.catalog-section:hover{background:var(--vp-c-default-soft)}
.catalog-section>span{flex:1}
.catalog-section small{font:10px var(--vp-font-family-mono);color:var(--vp-c-text-3);white-space:nowrap;font-weight:400}
.section-chevron{width:13px;height:13px;color:var(--vp-c-text-3);transition:transform .15s}
.section-chevron.expanded{transform:rotate(90deg)}
.catalog-items{padding:1px 0}
.catalog-item{display:flex;align-items:center;gap:8px;width:100%;padding:8px 10px 8px 25px;border-radius:7px;text-align:left;color:var(--vp-c-text-1);font-size:13px;line-height:21px}
.catalog-item:hover{background:var(--vp-c-default-soft)}
.catalog-item.active{background:#edf7ff;color:#0087be}
.item-icon{width:16px;height:16px;color:var(--vp-c-text-3);stroke-width:1.3}
.item-icon.done,.catalog-item.active .item-icon{color:#0087be}
.catalog-empty{padding:24px 12px;font-size:13px;color:var(--vp-c-text-3)}
button:focus-visible{outline:2px solid #0087be;outline-offset:-2px}
.dark .catalog-scrim{background:#0003}
.dark .catalog-item.active{background:#20374a;color:#78c6f2}
.dark .item-icon.done,.dark .catalog-item.active .item-icon{color:#78c6f2}
@media(max-width:600px){.course-catalog{left:50px;bottom:8px;max-width:calc(100vw - 60px);border-radius:10px}.catalog-section{font-size:12px}}
@media(prefers-reduced-motion:reduce){.section-chevron{transition:none}}
</style>
