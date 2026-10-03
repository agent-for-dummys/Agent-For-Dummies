<script setup lang="ts">
import localSearchIndex from '@localSearchIndex';
import MiniSearch from 'minisearch';
import { useData, useRouter } from 'vitepress';
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { highlight, rankArticles, type ArticleResult, type SectionHit } from './search-ranking';

const { theme, localeIndex } = useData();
const router = useRouter();
const dialog = ref<HTMLDialogElement>();
const input = ref<HTMLInputElement>();
const query = ref('');
const ready = ref(false);
const loading = ref(false);
const failed = ref(false);
const selected = ref(0);
const opened = ref(false);
let engine: MiniSearch | null = null;
let pending: Promise<void> | null = null;
let previousFocus: HTMLElement | null = null;
let previousOverflow = '';
let indexModules = localSearchIndex;

if (import.meta.hot) {
  import.meta.hot.accept('/@localSearchIndex', module => {
    if (module) { indexModules = module.default; engine = null; ready.value = false; if (opened.value) void loadIndex(); }
  });
}

async function loadIndex() {
  if (engine || pending) return pending;
  loading.value = true;
  failed.value = false;
  pending = (async () => {
    try {
      const content = (await indexModules[localeIndex.value]?.())?.default;
      if (!content) throw new Error('Missing search index');
      const options = theme.value.search?.options?.miniSearch;
      engine = MiniSearch.loadJSON(content, {
        fields: ['title', 'titles', 'text'],
        storeFields: ['title', 'titles', 'text'],
        ...options?.options,
        searchOptions: options?.searchOptions
      });
      ready.value = true;
    } catch {
      failed.value = true;
    } finally {
      loading.value = false;
      pending = null;
    }
  })();
  return pending;
}

const results = computed(() => ready.value && engine && query.value.trim() ? rankArticles(engine.search(query.value.trim()) as unknown as SectionHit[], query.value) : []);

async function openSearch() {
  if (opened.value) { input.value?.focus(); return; }
  previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  query.value = '';
  selected.value = 0;
  opened.value = true;
  previousOverflow = document.documentElement.style.overflow;
  document.documentElement.style.overflow = 'hidden';
  dialog.value?.showModal();
  await nextTick();
  input.value?.focus();
  void loadIndex();
}

function closeSearch() {
  dialog.value?.getAnimations({ subtree: true }).forEach(animation => animation.cancel());
  dialog.value?.close();
  document.documentElement.style.overflow = previousOverflow;
  opened.value = false;
  previousFocus?.focus({ preventScroll: true });
}

function navigate(result: ArticleResult) {
  closeSearch();
  void router.go(result.href);
}

function keyboard(event: KeyboardEvent) {
  if (opened.value && event.key === 'Escape') {
    event.preventDefault();
    event.stopImmediatePropagation();
    closeSearch();
    return;
  }
  const editing = event.target instanceof Element && (event.target.closest('input, textarea, select') || (event.target as HTMLElement).isContentEditable);
  if ((event.key.toLowerCase() === 'k' && (event.ctrlKey || event.metaKey)) || (event.key === '/' && !editing && !opened.value)) {
    event.preventDefault();
    event.stopImmediatePropagation();
    void openSearch();
  } else if (opened.value && ['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key) && results.value.length && event.target === input.value) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.key === 'Enter') navigate(results.value[selected.value]);
    else selected.value = (selected.value + (event.key === 'ArrowDown' ? 1 : -1) + results.value.length) % results.value.length;
  }
}

function outside(event: MouseEvent) {
  if (event.target !== dialog.value) return;
  const box = dialog.value.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closeSearch();
}

watch(query, () => { selected.value = 0; });
watch(results, async (current, previous) => {
  const previousPages = new Set(previous.map(result => result.page));
  const entering = new Set(current.filter(result => !previousPages.has(result.page)).map(result => result.page));
  await nextTick();
  if (!opened.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  dialog.value?.querySelectorAll<HTMLElement>('li[data-page]').forEach((element, index) => {
    if (entering.has(element.dataset.page!)) element.animate(
      [{ opacity: 0, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 190, delay: Math.min(index, 5) * 24, easing: 'ease-out', fill: 'backwards' }
    );
  });
});
watch(selected, async () => { await nextTick(); dialog.value?.querySelector(`#note-result-${selected.value}`)?.scrollIntoView({ block: 'nearest' }); });
onMounted(() => window.addEventListener('keydown', keyboard, true));
onUnmounted(() => { window.removeEventListener('keydown', keyboard, true); if (opened.value) closeSearch(); });
</script>

<template>
  <div class="notebook-search">
    <button class="notebook-search-trigger" type="button" aria-label="全文搜索笔记" @click="openSearch">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>
      <span>搜索笔记</span><kbd>Ctrl K</kbd>
    </button>
    <dialog ref="dialog" class="notebook-search-dialog" aria-label="全文搜索笔记" @cancel.prevent="closeSearch" @click="outside">
      <div class="notebook-search-input">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>
        <input ref="input" v-model="query" type="search" autocomplete="off" placeholder="搜索章节、概念或代码" aria-label="搜索关键词" role="combobox" :aria-expanded="opened" aria-controls="notebook-search-results" :aria-activedescendant="results.length ? `note-result-${selected}` : undefined">
        <button type="button" aria-label="关闭搜索" class="notebook-search-close" @click="closeSearch">Esc</button>
      </div>
      <p v-if="loading" class="notebook-search-message" role="status">正在搜索…</p>
      <div v-else-if="failed" class="notebook-search-message" role="alert">暂时无法搜索 <button type="button" @click="loadIndex">重试</button></div>
      <p v-else-if="query.trim() && !results.length" class="notebook-search-message" role="status">没有找到相关内容</p>
      <ul id="notebook-search-results" class="notebook-search-results" role="listbox" aria-label="搜索结果">
        <li v-for="(result, index) in results" :id="`note-result-${index}`" :key="result.page" role="option" :aria-selected="selected === index" :data-page="result.page" :class="{ selected: selected === index }">
          <a :href="result.href" @click.prevent="navigate(result)" @pointermove="selected = index">
            <div class="notebook-search-result-title"><span><template v-for="(part, i) in highlight(result.title, query)" :key="i"><mark v-if="part.matched">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span><span class="notebook-search-category">{{ result.category }}</span></div>
            <p v-if="result.section" class="notebook-search-section"><template v-for="(part, i) in highlight(result.section, query)" :key="i"><mark v-if="part.matched">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></p>
            <p v-if="result.snippet" class="notebook-search-snippet"><template v-for="(part, i) in highlight(result.snippet, query)" :key="i"><mark v-if="part.matched">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></p>
          </a>
        </li>
      </ul>
      <footer class="notebook-search-footer"><span>↑ ↓ 选择　↵ 打开</span><span aria-live="polite">{{ query.trim() ? `${results.length} 篇` : '12 篇笔记' }}</span></footer>
      <div class="notebook-search-effects" aria-hidden="true"></div>
    </dialog>
  </div>
</template>
