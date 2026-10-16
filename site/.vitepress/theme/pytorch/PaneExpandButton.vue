<script setup lang="ts">
defineProps<{expanded:boolean;label:string}>();
defineEmits<{toggle:[]}>();
</script>
<template>
 <button type="button" class="pane-expand" :aria-label="expanded?'还原布局':`铺满${label}`" :title="expanded?'还原布局':`铺满${label}`" :aria-pressed="expanded" @click="$emit('toggle')">
  <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path :d="expanded?'M3 7h4V3M13 3v4h4M17 13h-4v4M7 17v-4H3':'M7 3H3v4M13 3h4v4M17 13v4h-4M7 17H3v-4'" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
 </button>
</template>
<style scoped>
.pane-expand{display:inline-flex;align-items:center;justify-content:center;flex:0 0 26px;width:26px;height:28px;padding:0!important;align-self:center;border:0!important;border-radius:4px;color:var(--vp-c-text-2);background:transparent;cursor:pointer}
.pane-expand svg{flex-shrink:0}
.pane-expand:hover{background:var(--lab-blue-soft);color:var(--lab-blue)}
.pane-expand:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
</style>
