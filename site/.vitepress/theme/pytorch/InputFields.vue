<script setup lang="ts">
import { computed } from 'vue';
import { pythonValue } from './format';
const props=defineProps<{input:unknown;parameters:{name:string}[]}>();
const fields=computed(()=>props.parameters.map((p,i)=>{
 const value=(props.input as any[])?.[i];
 const tensor=value&&typeof value==='object'&&!Array.isArray(value)&&Array.isArray(value.shape)&&'dtype' in value&&'data' in value;
 return {name:p.name,text:pythonValue(tensor&&!value.truncated?value.data:value),metadata:tensor?`${value.dtype} · [${value.shape.join(', ')}]`:''};
}));
</script>
<template><div class="input-fields"><div v-for="field in fields" :key="field.name" class="input-field"><h4><code>{{ field.name }} =</code><span v-if="field.metadata">{{ field.metadata }}</span></h4><pre>{{ field.text }}</pre></div></div></template>
<style scoped>
.input-field{margin:0 0 18px;min-width:0}.input-field h4{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;margin:0 0 8px;font-size:13px;font-weight:500;color:var(--vp-c-text-2)}.input-field code{background:transparent;font:13px var(--vp-font-family-mono);color:var(--vp-c-text-1)}.input-field h4 span{font:11px var(--vp-font-family-mono);color:var(--vp-c-text-3)}.input-field pre{font:14px/1.8 var(--vp-font-family-mono);font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0;margin:0;padding:10px 13px;white-space:pre;overflow:auto;background:var(--vp-c-bg);border:1px solid var(--vp-c-divider);border-radius:7px;color:var(--vp-c-text-1)}
</style>
