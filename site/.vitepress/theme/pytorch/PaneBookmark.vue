<script setup lang="ts">
defineProps<{side:'left'|'right';label:string}>();
defineEmits<{restore:[]}>();
</script>
<template>
 <div class="bookmark-rail">
  <button type="button" class="pane-bookmark" :aria-label="`恢复${label}区`" :title="`恢复${label}区`" @click="$emit('restore')">
   <svg width="14" height="14" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path :d="side==='left'?'M7 4l6 6-6 6':'M13 4l-6 6 6 6'" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
   <span>{{ label }}</span>
  </button>
 </div>
</template>
<style scoped>
.bookmark-rail{display:flex;align-items:center;justify-content:center;min-width:0;min-height:0}
.pane-bookmark{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;width:28px;padding:13px 0;border:1px solid var(--vp-c-border);border-radius:6px;background:var(--vp-c-bg);color:var(--lab-blue);cursor:pointer}
.pane-bookmark span{writing-mode:vertical-rl;font-size:13px;font-weight:500;line-height:1;letter-spacing:2px}
.pane-bookmark:hover{background:var(--lab-blue-soft);border-color:var(--lab-blue)}
.pane-bookmark:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
</style>
