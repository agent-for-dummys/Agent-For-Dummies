<script setup lang="ts">
import {ref} from 'vue';
import ProjectTree from './ProjectTree.vue';

withDefaults(defineProps<{files: string[]; filename: string; expandedFolders?: string[]}>(), {
  expandedFolders: () => [],
});
const emit = defineEmits<{select: [file: string]; toggle: [folder: string]}>();
const filesOpen = ref(false);
</script>

<template>
  <div class="editor-card">
    <header class="editor-toolbar">
      <button type="button" class="file-toggle" :aria-label="filesOpen ? '收起文件栏' : '展开文件栏'" :aria-expanded="filesOpen" @click="filesOpen = !filesOpen">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M2 5h6l2 2h8v10H2z" stroke="currentColor" stroke-linejoin="round"/><path d="M2 5V3h6l2 2" stroke="currentColor"/></svg>
      </button>
      <span class="editor-filename" :title="filename">{{ filename.split('/').pop() }}</span>
      <slot name="actions"/>
    </header>
    <div class="editor-body">
      <aside v-if="filesOpen" class="file-explorer" aria-label="项目文件">
        <ProjectTree :files="files" :selected="filename" :expanded="expandedFolders" @select="emit('select', $event)" @toggle="emit('toggle', $event)"/>
      </aside>
      <div class="code-surface"><slot/></div>
    </div>
  </div>
</template>

<style scoped>
.editor-card{border:1px solid var(--vp-c-divider);border-radius:10px;overflow:hidden;background:var(--vp-c-bg)}
.editor-toolbar{display:flex;align-items:center;min-height:48px;padding:6px 10px;border-bottom:1px solid var(--vp-c-divider);flex:none}
.editor-card{display:flex;flex-direction:column;flex:1;min-height:150px}.editor-toolbar{gap:9px}.file-toggle{display:flex;align-items:center;justify-content:center;width:24px;height:28px;color:var(--vp-c-text-2)}
.editor-filename{font:12px var(--vp-font-family-mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.editor-body{display:flex;flex:1;min-height:0;position:relative}.file-explorer{flex:none;width:170px;overflow:auto;background:var(--vp-code-bg);padding:10px 6px;border-right:1px solid var(--vp-c-divider)}.code-surface{flex:1;min-width:0;min-height:0}.code-surface :deep(.cm-gutters){background:var(--vp-c-bg)}
@media(max-width:850px){.file-explorer{position:absolute;inset:0 auto 0 0;z-index:5;width:190px;box-shadow:4px 0 15px #00000012}}
</style>
