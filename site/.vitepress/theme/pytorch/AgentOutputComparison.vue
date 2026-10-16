<script setup lang="ts">
withDefaults(defineProps<{expected:string;actual?:string;expectedLabel?:string;state?:'pass'|'fail'|'pending'|'neutral'}>(),{expectedLabel:'预期输出',state:'neutral'});
</script>
<template>
 <div class="agent-output-comparison">
  <div class="data-field"><h4>{{expectedLabel}}</h4><pre>{{expected}}</pre></div>
  <div class="data-field actual-output" :class="state"><h4>实际输出</h4><pre class="live-text">{{actual??(state==='pending'?'':'未返回结果。')}}</pre></div>
 </div>
</template>
<style scoped>
.agent-output-comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px;align-items:start;margin-bottom:16px}
.data-field{min-width:0}.data-field h4{margin:0 0 8px;padding:0;border:0;font-size:13px;font-weight:500;line-height:1.6;color:var(--vp-c-text-2)}
.data-field pre{font:14px/1.8 var(--vp-font-family-mono);font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0;margin:0;padding:10px 13px;border:1px solid var(--vp-c-divider);border-radius:7px;white-space:pre-wrap;overflow:auto;overflow-wrap:anywhere;background:var(--vp-code-bg);color:var(--vp-c-text-1)}
.actual-output.pass pre{color:var(--lab-blue);background:var(--lab-blue-soft)}.actual-output.pass h4{color:var(--lab-blue)}
.actual-output.fail pre{color:var(--lab-red);background:var(--lab-red-soft)}.actual-output.fail h4{color:var(--lab-red)}
@container(max-width:520px){.agent-output-comparison{grid-template-columns:minmax(0,1fr)}}
</style>
