<script setup lang="ts">
import { computed } from 'vue';
const props=defineProps<{level:string;small?:boolean}>();
const label=computed(()=>props.level==='入门'?'简单':props.level);
const grade=computed(()=>label.value==='简单'?'easy':label.value==='中等'?'medium':'hard');
</script>
<template><span :class="['level-dot',grade,{small}]" role="img" :aria-label="`难度：${label}`" :title="label"/></template>
<style scoped>.level-dot{display:inline-block;width:10px;height:10px;border-radius:50%;flex-shrink:0;align-self:center}.easy{background:#22b46c}.medium{background:#e1a128}.hard{background:#e56670}.small{width:6px;height:6px}</style>
