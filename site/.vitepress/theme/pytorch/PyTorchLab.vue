<script setup lang="ts">
import {computed, KeepAlive, nextTick, onMounted, onUnmounted, ref} from 'vue';
import pytorch from '../../../../oj/course.json';
import agent from '../../../../oj/agent_course.json';
import CourseWorkspace from './CourseWorkspace.vue';
import AgentWorkspace from './AgentWorkspace.vue';
import CourseRoadmap from './CourseRoadmap.vue';
import CourseCatalog from './CourseCatalog.vue';
import {agentMap, pytorchMap, type NavigationState, type Track} from './course-navigation';
import {prepareLearningPage} from './editor-runtime';

type Workspace = {selectTarget: (id: string) => boolean | Promise<boolean>};
const track = ref<Track>('agent');
const mapOpen = ref(true), catalogOpen = ref(false);
const navBottom = ref(64), bookmarkTop = ref(168);
const workspace = ref<Workspace>();
const state = ref<Record<Track, NavigationState>>({
  agent: {selected: agent.chapters[0].id, completed: []},
  pytorch: {selected: 'module:' + pytorch.modules[0].id, completed: []},
});
const maps = {agent: agentMap(agent), pytorch: pytorchMap(pytorch)};
const currentMap = computed(() => maps[track.value]);
const currentState = computed(() => state.value[track.value]);
let navObserver: ResizeObserver | undefined;

function measure() {
  navBottom.value = Math.max(0, document.querySelector('.VPNav')?.getBoundingClientRect().bottom || 64);
  const selector = track.value === 'agent' ? '.agent-ide .learning-content h1' : '.pytorch-lab .pane-title,.pytorch-lab .question-heading h2';
  const title = document.querySelector<HTMLElement>(selector);
  const bounds = title?.getBoundingClientRect();
  bookmarkTop.value = !mapOpen.value && bounds && bounds.height > 0
    ? Math.max(navBottom.value + 70, Math.min(bounds.top + bounds.height / 2 - 22, window.innerHeight - 110))
    : navBottom.value + 108;
}
function updateState(course: Track, next: NavigationState) {
  state.value = {...state.value, [course]: next};
  nextTick(measure);
}
async function switchCourse(next: Track) {
  if (next === track.value) return;
  catalogOpen.value = false;
  track.value = next;
  localStorage.setItem('learning-course', next);
  const url = new URL(location.href);
  url.searchParams.set('course', next);
  history.replaceState(history.state, '', url);
  await nextTick();
  measure();
}
async function selectTarget(id: string) {
  await prepareLearningPage();
  if (await workspace.value?.selectTarget(id) === false) return;
  mapOpen.value = false;
  catalogOpen.value = false;
  await nextTick();
  measure();
}
function toggleMap() {
  catalogOpen.value = false;
  mapOpen.value = !mapOpen.value;
  nextTick(measure);
}
function toggleCatalog() {
  mapOpen.value = false;
  catalogOpen.value = !catalogOpen.value;
  nextTick(measure);
}
function key(event: KeyboardEvent) {
  if (event.key !== 'Escape' || document.querySelector('dialog[open],.VPLocalSearchBox')) return;
  if (catalogOpen.value) catalogOpen.value = false;
  else if (mapOpen.value) mapOpen.value = false;
  nextTick(measure);
}
function practiceLink(event: MouseEvent) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const anchor = (event.target as HTMLElement).closest<HTMLAnchorElement>('.VPNav a');
  if (!anchor || anchor.target === '_blank') return;
  const url = new URL(anchor.href);
  if (url.origin !== location.origin || url.pathname !== location.pathname) return;
  event.preventDefault();
  catalogOpen.value = false;
  mapOpen.value = true;
  switchCourse('agent');
  nextTick(measure);
}
onMounted(() => {
  const requested = new URLSearchParams(location.search).get('course');
  track.value = requested === 'pytorch' ? 'pytorch' : 'agent';
  measure();
  navObserver = new ResizeObserver(measure);
  const nav = document.querySelector('.VPNav');
  if (nav) navObserver.observe(nav);
  window.addEventListener('resize', measure);
  document.addEventListener('keydown', key);
  document.addEventListener('click', practiceLink, true);
});
onUnmounted(() => {
  navObserver?.disconnect();
  window.removeEventListener('resize', measure);
  document.removeEventListener('keydown', key);
  document.removeEventListener('click', practiceLink, true);
});
</script>

<template>
  <div class="practice-shell" :data-track="track">
    <div v-show="!mapOpen" class="practice-workspace">
      <KeepAlive>
        <AgentWorkspace v-if="track==='agent'" ref="workspace" key="agent" @navigation="updateState('agent',$event)"/>
        <CourseWorkspace v-else ref="workspace" key="pytorch" track="pytorch" :course="pytorch" @navigation="updateState('pytorch',$event)"/>
      </KeepAlive>
    </div>
    <CourseRoadmap v-if="mapOpen" :key="track" :map="currentMap" :track="track" :completed="currentState.completed" :nav-bottom="navBottom" @select="selectTarget" @close="mapOpen=false"/>
    <nav v-if="mapOpen" class="map-course-switch" :style="{top: (navBottom+24)+'px'}" aria-label="切换学习课程">
      <button v-for="course in [{id:'agent',name:'Agent'},{id:'pytorch',name:'PyTorch'}]" :key="course.id" type="button" :class="{active:track===course.id}" :aria-pressed="track===course.id" @click="switchCourse(course.id as Track)">{{course.name}}</button>
    </nav>
    <CourseCatalog v-if="catalogOpen" :key="track" :track="track" :sections="currentMap.sections" :state="currentState" :nav-bottom="navBottom" @select="selectTarget" @close="catalogOpen=false"/>
    <nav class="practice-bookmarks" :style="{top: bookmarkTop+'px'}" aria-label="练习导航">
      <button type="button" :class="{active:mapOpen}" :aria-pressed="mapOpen" :aria-expanded="mapOpen" aria-controls="course-roadmap" :aria-label="mapOpen?'收起学习路线图':'展开学习路线图'" @click="toggleMap">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="5" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M7.5 5H16a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h8.5"/></svg>
        <span>学习路线</span>
      </button>
      <button type="button" :class="{active:catalogOpen}" :aria-pressed="catalogOpen" :aria-expanded="catalogOpen" aria-controls="course-catalog" :aria-label="catalogOpen?'收起题目列表':'展开题目列表'" @click="toggleCatalog">
        <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="3.5" width="16" height="17" rx="2"/><path d="M8.5 3.5v17M12 8h4.5M12 12h4.5M12 16h3"/></svg>
        <span>题目列表</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
.practice-shell{--lab-blue:#0087be;--lab-blue-soft:#edf7ff;min-height:calc(100dvh - 120px)}
.practice-workspace{padding-left:34px}
.practice-bookmarks{position:fixed;left:0;z-index:42;display:flex;flex-direction:column;align-items:flex-start;gap:12px;width:42px;pointer-events:none}
.practice-bookmarks button{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:8px;width:34px;height:112px;padding:12px 0;border:1px solid var(--vp-c-divider);border-left:0;border-radius:0 10px 10px 0;background:var(--vp-c-bg);color:var(--vp-c-text-2);box-shadow:1px 2px 6px #263d5b08;pointer-events:auto;transition:width .18s ease,background .18s,color .18s,border-color .18s,box-shadow .18s}
.practice-bookmarks button:hover{color:var(--lab-blue);border-color:#a9cfe2}
.practice-bookmarks button.active{width:42px;border-color:var(--lab-blue);background:var(--lab-blue);color:#fff;box-shadow:2px 3px 8px #0087be24}
.practice-bookmarks svg{width:19px;height:19px;flex:none;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.practice-bookmarks span{writing-mode:vertical-rl;text-orientation:upright;font-size:12px;line-height:16px;letter-spacing:2px;font-weight:500;white-space:nowrap}
.map-course-switch{position:fixed;left:80px;z-index:30;display:flex;gap:4px;padding:4px;border:1px solid var(--vp-c-divider);border-radius:10px;background:var(--vp-c-bg-soft)}
.map-course-switch button{min-width:84px;padding:7px 17px;border-radius:7px;font-size:13px;font-weight:500;color:var(--vp-c-text-2)}
.map-course-switch button.active{background:var(--vp-c-bg);color:var(--lab-blue);box-shadow:0 1px 4px #1c36551a}
.practice-shell button:focus-visible{outline:2px solid var(--lab-blue);outline-offset:3px}
:global(.dark) .practice-shell{--lab-blue:#1688b9;--lab-blue-soft:#20374a}
@media(min-width:1720px){.practice-workspace{padding-left:12px}}
@media(max-width:600px){.practice-workspace{padding-left:40px}.practice-bookmarks{width:40px;gap:10px}.practice-bookmarks button{width:32px;height:104px;padding:10px 0}.practice-bookmarks button.active{width:40px}.practice-bookmarks span{font-size:11px;letter-spacing:1.5px}.map-course-switch{left:64px}}
@media(prefers-reduced-motion:reduce){.practice-bookmarks button{transition:none}}
</style>
