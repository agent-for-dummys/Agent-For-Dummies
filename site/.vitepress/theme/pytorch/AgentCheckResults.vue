<script setup lang="ts">
import {computed,ref,watch} from 'vue';
import ErrorFeedback from './ErrorFeedback.vue';
import AgentInputFields,{type AgentField} from './AgentInputFields.vue';
import AgentOutputComparison from './AgentOutputComparison.vue';
type CheckCase={name:string;status:string;message?:string;inputs?:AgentField[];expected?:string;expectedLabel?:string;actual?:string};
const props=defineProps<{result:{verdict:string;message?:string;cases:CheckCase[]}}>();
const index=ref(0);
const selected=computed(()=>props.result.cases[index.value]);
const passed=computed(()=>props.result.cases.filter(item=>item.status==='passed').length);
watch(()=>props.result,()=>{const failed=props.result.cases.findIndex(item=>item.status!=='passed');index.value=failed<0?0:failed;},{immediate:true});
function move(event:KeyboardEvent){
 const count=props.result.cases.length;
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)||!count)return;
 event.preventDefault();index.value=event.key==='Home'?0:event.key==='End'?count-1:(index.value+(event.key==='ArrowRight'?1:-1)+count)%count;
 (event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('button')[index.value]?.focus();
}
</script>
<template>
 <div class="agent-check-results">
  <div class="case-tabs" role="tablist" aria-label="选择测试用例" @keydown="move">
   <button v-for="(item,i) in result.cases" :key="i" type="button" role="tab" :aria-selected="index===i" :tabindex="index===i?0:-1" :aria-label="`用例 ${i+1}：${item.name}`" :class="{active:index===i,pass:item.status==='passed',fail:item.status!=='passed'}" @click="index=i">用例 {{i+1}}</button>
  </div>
  <div v-if="result.verdict==='AC'" class="run-status pass">Accepted<span class="score">{{passed}} / {{result.cases.length}}</span></div>
  <ErrorFeedback v-else :verdict="result.verdict" :message="selected?.message||result.message"/>
  <div v-if="selected" class="case-content" role="tabpanel" :aria-label="`用例 ${index+1}：${selected.name}`">
   <AgentInputFields :fields="selected.inputs||[]"/>
   <AgentOutputComparison v-if="selected.expected!==undefined||selected.actual!==undefined" :expected="selected.expected||''" :expected-label="selected.expectedLabel||'预期输出'" :actual="selected.actual" :state="selected.status==='passed'?'pass':'fail'"/>
  </div>
 </div>
</template>
<style scoped>
.case-tabs{display:flex;gap:3px;flex-wrap:wrap;width:fit-content;max-width:100%;padding:4px;margin-bottom:17px;border-radius:8px;background:var(--vp-code-bg)}
.case-tabs button{padding:6px 12px;border:0;border-radius:5px;font:500 13px/1.6 var(--vp-font-family-base);color:var(--vp-c-text-2);cursor:pointer}
.case-tabs button.active{background:var(--vp-c-bg);box-shadow:0 1px 3px #00000010}
.case-tabs button.active.pass{background:var(--lab-blue-soft)}.case-tabs button.active.fail{background:var(--lab-red-soft)}
.pass,.case-tabs button.pass{color:var(--lab-blue)}.fail,.case-tabs button.fail{color:var(--lab-red)}
.case-tabs button:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
.run-status{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:600;margin:4px 0 17px}.score{font-size:13px;font-weight:400;margin-left:5px}
.case-content{font-size:13px;line-height:1.8;color:var(--vp-c-text-2)}
</style>
