<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { type JudgeResult } from './api';
import { outputText } from './format';
import PaneExpandButton from './PaneExpandButton.vue';
import InputFields from './InputFields.vue';
import ErrorFeedback from './ErrorFeedback.vue';
const props=defineProps<{
 tab:'cases'|'result'; contextKey:string; lessonMode:boolean;
 problem:{parameters:{name:string}[];examples:{input:unknown;output:unknown}[];outputNames?:string[]};
 lesson:{input:string;output:string}; result?:JudgeResult;
 pending:boolean;jobStatus:string;connectionError:string;expanded:boolean;collapsed:boolean;
}>();
const emit=defineEmits<{'update:tab':[tab:'cases'|'result'];retry:[];expand:[];reveal:[];'header-height':[height:number]}>();
const header=ref<HTMLElement>();let headerObserver:ResizeObserver|undefined;
onMounted(()=>{if(header.value){headerObserver=new ResizeObserver(()=>{const height=header.value!.getBoundingClientRect().height;if(height>0)emit('header-height',height);});headerObserver.observe(header.value);}});
onUnmounted(()=>headerObserver?.disconnect());
function selectTab(tab:'cases'|'result'){emit('update:tab',tab);emit('reveal');}
const caseIndex=ref(0);
const tests=computed(()=>props.result?.cases.filter(test=>test.public||test.status!=='passed')||[]);
const selectedTest=computed(()=>tests.value[caseIndex.value]);
const selectedExample=computed(()=>props.problem.examples[caseIndex.value]);
const currentInput=computed(()=>props.tab==='result'?selectedTest.value?.input??selectedExample.value?.input:selectedExample.value?.input);
const expected=computed(()=>props.tab==='result'?selectedTest.value?.expected??selectedExample.value?.output:selectedExample.value?.output);
const normalized=(value:string)=>value.replace(/\r\n/g,'\n').trimEnd();
const lessonMatch=computed(()=>props.result?.verdict==='OK'&&normalized(props.result.stdout||'')===normalized(props.lesson.output));
const matches=(test:any)=>test?.matchesExpected??test?.status==='passed';
const hasResult=computed(()=>!!props.result&&!props.pending);
const pendingLabel=computed(()=>props.jobStatus==='connecting'?'连接中…':props.jobStatus==='queued'?'排队中…':'运行中…');
watch(()=>props.contextKey,()=>caseIndex.value=0);
watch(()=>props.tab,()=>caseIndex.value=0);
watch(()=>props.result,()=>{const failed=tests.value.findIndex(test=>!matches(test));caseIndex.value=failed>=0?failed:0;});
</script>

<template>
 <section class="run-panel" :class="{'header-only':collapsed}" aria-label="测试用例与运行结果">
  <nav ref="header" class="run-tabs" aria-label="运行区域">
   <button type="button" :class="{active:tab==='cases'}" @click="selectTab('cases')">{{ lessonMode?'示例数据':'测试用例' }}</button>
   <button type="button" :class="{active:tab==='result'}" @click="selectTab('result')">运行结果</button>
   <span v-if="hasResult&&tab==='result'&&result?.elapsedMs!==undefined" class="elapsed">{{ result.elapsedMs }} ms</span>
   <span class="run-actions"><slot name="actions"/></span>
   <PaneExpandButton :expanded="expanded" label="测试区" @toggle="emit('expand')"/>
  </nav>
  <div v-show="!collapsed" class="run-scroll" aria-live="polite">
   <p v-if="connectionError" class="connection-error">{{ connectionError }} <button type="button" @click="emit('retry')">重试</button></p>
   <template v-if="lessonMode">
    <template v-if="tab==='cases'"><div class="data-field"><h4>输入</h4><pre>{{ lesson.input }}</pre></div><div class="data-field"><h4>预期输出</h4><pre>{{ lesson.output }}</pre></div></template>
    <template v-else-if="pending"><p class="pending">{{ pendingLabel }}</p></template>
    <template v-else-if="result">
     <div v-if="lessonMatch" class="run-status pass"><span>✓</span>Passed</div><ErrorFeedback v-else :verdict="result.verdict==='OK'?'WA':result.verdict" :message="result.message" :line="result.line"/>
     <div class="output-comparison"><div class="data-field"><h4>预期输出</h4><pre>{{ lesson.output }}</pre></div><div :class="['data-field','actual-output',lessonMatch?'pass':'fail']"><h4>实际输出</h4><pre>{{ result.stdout||'没有标准输出。' }}</pre></div></div>
    </template><p v-else class="empty-result">运行示例后查看结果。</p>
   </template>
   <template v-else>
    <div v-if="tab==='cases'||hasResult&&tests.length" class="case-tabs" aria-label="选择测试用例"><button v-for="(_,i) in tab==='cases'?problem.examples:tests" :key="i" type="button" :class="{active:caseIndex===i,pass:tab==='result'&&matches(tests[i]),fail:tab==='result'&&!matches(tests[i])}" @click="caseIndex=i">{{ i<2?`用例 ${i+1}`:tests[i].name }}</button></div>
    <template v-if="tab==='cases'"><InputFields :input="currentInput" :parameters="problem.parameters"/><div class="data-field"><h4>预期输出</h4><pre>{{ outputText(expected,problem) }}</pre></div></template>
    <p v-else-if="pending" class="pending">{{ pendingLabel }}</p>
    <template v-else-if="result">
     <div v-if="result.verdict==='AC'" class="run-status pass">Accepted<span v-if="result.total" class="score">{{ result.passed }} / {{ result.total }}</span></div><ErrorFeedback v-else :verdict="result.verdict" :message="selectedTest?.message||result.message" :line="selectedTest?.line||result.line"/>
     <template v-if="selectedTest"><InputFields v-if="currentInput!==undefined" :input="currentInput" :parameters="problem.parameters"/><div class="output-comparison"><div v-if="expected!==undefined" class="data-field"><h4>预期输出</h4><pre>{{ outputText(expected,problem) }}</pre></div><div :class="['data-field','actual-output',matches(selectedTest)?'pass':'fail']"><h4>实际输出</h4><pre>{{ selectedTest.actual===undefined?'未返回结果。':outputText(selectedTest.actual,problem) }}</pre></div></div></template>
     <div v-if="result.stdout" class="data-field"><h4>标准输出</h4><pre>{{ result.stdout }}</pre></div>
    </template><p v-else class="empty-result">运行代码后查看结果。</p>
   </template>
  </div>
 </section>
</template>

<style scoped>
.run-panel{display:flex;flex-direction:column;flex-shrink:0;min-height:0;min-width:0;background:var(--vp-c-bg);overflow:hidden}
.run-panel.header-only .run-tabs{border-bottom:0}
.run-tabs{display:flex;align-items:center;flex-wrap:wrap;gap:8px;min-height:46px;padding:6px 10px;border-bottom:1px solid var(--vp-c-divider);flex-shrink:0}
.run-tabs>button{padding:5px 8px;font-size:14px;font-weight:500;white-space:nowrap;color:var(--vp-c-text-2);border:0;border-radius:5px}.run-tabs>button.active{color:var(--lab-blue);background:var(--lab-blue-soft)}
.elapsed{font:12px var(--vp-font-family-mono);align-self:center;margin-left:auto;color:var(--vp-c-text-3)}
.run-actions{display:flex;align-items:center;gap:7px;margin-left:auto}.elapsed{margin-left:0;font-variant-numeric:tabular-nums lining-nums}
.run-scroll{overflow:auto;flex:1;padding:16px 20px 22px;min-height:0}.case-tabs{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:17px}.case-tabs button{display:flex;align-items:center;gap:6px;padding:5px 11px;font-size:13px;font-weight:500;border-radius:5px;color:var(--vp-c-text-2)}.case-tabs button.active{background:var(--vp-code-bg)}.case-tabs button.active.pass{background:var(--lab-blue-soft)}.case-tabs button.active.fail{background:var(--lab-red-soft)}
.data-field{margin:0 0 16px}.run-panel h4{font-size:13px;font-weight:500;margin:0 0 8px;line-height:1.6;color:var(--vp-c-text-2)}.run-panel pre{font:14px/1.8 var(--vp-font-family-mono);margin:0;padding:10px 13px;border:0;border-radius:5px;white-space:pre;overflow:auto;background:var(--vp-code-bg);color:var(--vp-c-text-1)}
.run-status{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:600;margin:4px 0 17px}.score{font-size:13px;font-weight:400;margin-left:5px}.pass,.case-tabs button.pass{color:var(--lab-blue)}.fail,.case-tabs button.fail{color:var(--lab-red)}.actual-output.pass pre{color:var(--lab-blue);background:var(--lab-blue-soft)}.actual-output.fail pre{color:var(--lab-red);background:var(--lab-red-soft)}.actual-output.pass h4{color:var(--lab-blue)}.actual-output.fail h4{color:var(--lab-red)}
.run-panel .failure-reason,.run-panel .connection-error{font-size:14px;line-height:1.8;color:var(--lab-red);margin:8px 0 16px}.connection-error button{color:var(--lab-blue)}.run-panel .empty-result,.run-panel .pending{font-size:14px;line-height:1.8;margin:10px 0;color:var(--vp-c-text-3)}.run-panel button:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
@container(max-width:470px){.run-tabs{gap:5px;padding:6px 8px}.run-tabs>button{padding:5px;font-size:13px}.elapsed{display:none}.run-actions{gap:5px}}
@media(max-width:600px){.run-scroll{padding:14px 15px 20px}.elapsed{display:none}}
.case-tabs{display:flex;gap:3px;flex-wrap:wrap;width:fit-content;max-width:100%;padding:4px;border-radius:8px;background:var(--vp-code-bg)}.case-tabs button{border-radius:5px;padding:6px 12px}.case-tabs button.active{background:var(--vp-c-bg);box-shadow:0 1px 3px #00000010}.output-comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px;align-items:start}.output-comparison .data-field{min-width:0}.data-field pre{border:1px solid var(--vp-c-divider);border-radius:7px}
@container(max-width:520px){.output-comparison{grid-template-columns:minmax(0,1fr)}}
</style>
