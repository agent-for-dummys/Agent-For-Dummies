<script setup lang="ts">
import {computed} from 'vue';
export interface AgentField {name:string;type?:string;text:string;editable?:boolean;aria?:string}
const props=defineProps<{fields:AgentField[]}>();
const visible=computed(()=>{
 const data=props.fields.filter(field=>!(['model','on_event','on_text','adapter_factory','embeddings','saver','checkpointer'].includes(field.name)&&field.text.startsWith('<')));
 return data.length?data:props.fields;
});
const emit=defineEmits<{edit:[value:string]}>();
</script>
<template>
 <div class="agent-input-fields">
  <div v-for="field in visible" :key="field.name" class="input-field">
   <h4><label v-if="field.editable" :for="'agent-input-'+field.name"><code>{{field.name}} =</code></label><code v-else>{{field.name}} =</code><span v-if="field.type">{{field.type}}</span></h4>
   <textarea v-if="field.editable" :id="'agent-input-'+field.name" class="question-input" :aria-label="field.aria||field.name" :value="field.text" :rows="Math.min(6,Math.max(1,field.text.split('\n').length))" maxlength="4000" @input="emit('edit',($event.target as HTMLTextAreaElement).value)"/>
   <pre v-else>{{field.text}}</pre>
  </div>
 </div>
</template>
<style scoped>
.agent-input-fields{min-width:0}.input-field{margin:0 0 18px;min-width:0}
.input-field h4{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;margin:0 0 8px;padding:0;border:0;font-size:13px;font-weight:500;line-height:1.6;color:var(--vp-c-text-2)}
.input-field code{padding:0;border:0;border-radius:0;background:transparent;font:13px var(--vp-font-family-mono);color:var(--vp-c-text-1)}
.input-field h4 span{font:11px var(--vp-font-family-mono);color:var(--vp-c-text-3)}
.input-field pre,.input-field textarea{display:block;width:100%;font:14px/1.8 var(--vp-font-family-mono);font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0;margin:0;padding:10px 13px;overflow:auto;background:var(--vp-c-bg);border:1px solid var(--vp-c-divider);border-radius:7px;color:var(--vp-c-text-1)}
.input-field pre{white-space:pre}.input-field textarea{resize:vertical;min-height:46px;white-space:pre-wrap;overflow-wrap:anywhere}
.input-field textarea:focus-visible{outline:2px solid var(--lab-blue);outline-offset:1px}
</style>
