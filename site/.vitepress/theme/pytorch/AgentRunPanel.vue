<script setup lang="ts">
import {computed} from 'vue';
import PaneExpandButton from './PaneExpandButton.vue';
import ErrorFeedback from './ErrorFeedback.vue';
import AgentCheckResults from './AgentCheckResults.vue';
import AgentInputFields from './AgentInputFields.vue';

const props=defineProps<{
 chapter:any;question:string;runQuestion?:string;tab:'cases'|'result';expanded:boolean;
 busy:boolean;status:string;message:string;result?:any;events:any[];
}>();
const emit=defineEmits<{
 'update:question':[value:string];'update:tab':[value:'cases'|'result'];
 expand:[];run:[mode:'check'|'live'|'run',approval?:boolean];cancel:[];
}>();
const text=computed(()=>props.events.filter(event=>event.type==='text').map(event=>event.text).join(''));
const toolEvents=computed(()=>props.events.filter(event=>event.type!=='text'));
const failure=computed(()=>props.result&&!['AC','OK','WAITING','CANCELLED'].includes(props.result.verdict));
const inputs=(question:string,editable=false)=>(props.chapter.panelInputs||[]).map((field:any)=>({...field,text:field.name===(props.chapter.inputLabel||'question')?question:field.text,editable:editable&&props.chapter.live&&field.name===(props.chapter.inputLabel||'question'),aria:props.chapter.inputAria||'模型输入'}));
const previewInputs=computed(()=>inputs(props.question,true));
const resultInputs=computed(()=>props.result?.inputs||inputs(props.runQuestion??props.question));
</script>
<template>
 <section class="run-panel" :class="{expanded}" aria-label="Agent 测试用例与运行结果">
  <nav class="run-tabs run-toolbar" aria-label="运行区域">
   <button type="button" :class="{active:tab==='cases'}" @click="emit('update:tab','cases')">测试用例</button>
   <button type="button" :class="{active:tab==='result'}" @click="emit('update:tab','result')">运行结果</button>
   <span v-if="tab==='result'&&!busy&&result?.elapsedMs!==undefined" class="elapsed">{{result.elapsedMs}} ms</span>
   <div class="run-actions">
    <template v-if="busy">
     <span class="job-status" role="status" :aria-label="status==='queued'?'等待中':'运行中'"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" opacity=".2"/><path d="M10 3a7 7 0 0 1 7 7"/></svg></span>
     <button type="button" class="stop-button" aria-label="停止运行" @click="emit('cancel')"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 3.8 16 10 6 16.2Z" fill="currentColor"/></svg></button>
    </template>
    <template v-else>
     <button type="button" class="run-button" @click="emit('run',chapter.live?'live':'run')">运行</button>
     <button v-if="chapter.id!=='intro'" type="button" class="primary-button" @click="emit('run','check')">提交</button>
    </template>
   </div>
   <PaneExpandButton :expanded="expanded" label="测试区" @toggle="emit('expand')"/>
  </nav>
  <div class="run-content run-scroll" aria-live="polite">
   <ErrorFeedback v-if="message" verdict="SYSTEM" :message="message"/>
   <template v-if="tab==='cases'">
    <AgentInputFields :fields="previewInputs" @edit="emit('update:question',$event)"/>
    <div class="data-field"><h4>{{chapter.live?'输出要求':'预期输出'}}</h4><pre>{{chapter.runtimeOutput||chapter.interface.example.output}}</pre></div>
   </template>
   <template v-else>
    <div v-if="result||busy||text" class="result-content">
     <AgentCheckResults v-if="result?.cases?.length" :result="result"/>
     <template v-else>
      <strong v-if="result&&['AC','WAITING','CANCELLED'].includes(result.verdict)" :class="{passed:result.verdict==='AC'}">{{result.verdict==='AC'?'Accepted':result.verdict==='WAITING'?'等待确认':'已停止'}}</strong>
      <ErrorFeedback v-if="failure" :verdict="result.verdict" :message="result.message"/>
      <AgentInputFields :fields="resultInputs"/>
      <div v-if="chapter.live&&(text||result?.verdict==='OK')" class="data-field actual-output" :class="{pass:!busy&&result?.verdict==='OK',fail:failure}"><h4>实际输出</h4><pre class="live-text">{{text}}</pre></div>
     </template>
     <div v-if="result?.interrupt" class="approval-box"><pre>{{JSON.stringify(result.interrupt.calls,null,2)}}</pre><button type="button" @click="emit('run','live',true)">确认执行</button><button type="button" @click="emit('run','live',false)">取消</button></div>
     <div v-if="result?.stdout" class="data-field"><h4>标准输出</h4><pre>{{result.stdout}}</pre></div>
    </div>
    <p v-else-if="!busy&&!text" class="empty-result">运行代码后查看结果。</p>
    <details v-if="toolEvents.length" class="event-details"><summary>工具与运行过程</summary><div v-for="(event,i) in toolEvents" :key="i" class="event-line"><span>{{event.name||event.type}}</span><pre v-if="event.text">{{event.text}}</pre></div></details>
   </template>
  </div>
 </section>
</template>
<style scoped>
.run-panel{display:flex;flex-direction:column;flex:none;min-height:48px;min-width:0;max-height:calc(100% - 160px);border:1px solid var(--vp-c-divider);border-radius:10px;background:var(--vp-c-bg);overflow:hidden;container-type:inline-size}
.run-panel.expanded{height:100%!important;flex:1;max-height:none}
.run-tabs{display:flex;align-items:center;flex-wrap:wrap;gap:8px;min-height:46px;padding:6px 10px;border-bottom:1px solid var(--vp-c-divider);flex-shrink:0}
.run-tabs>button{padding:5px 8px;font-size:14px;font-weight:500;white-space:nowrap;color:var(--vp-c-text-2);border:0;border-radius:5px;cursor:pointer}
.run-tabs>button.active{color:var(--lab-blue);background:var(--lab-blue-soft)}
.elapsed{font:12px var(--vp-font-family-mono);color:var(--vp-c-text-3);font-variant-numeric:tabular-nums}
.run-actions{display:flex;align-items:center;gap:7px;margin-left:auto}
.run-button,.primary-button{padding:5px 10px;border:1px solid var(--vp-c-divider);border-radius:5px;font-size:14px;font-weight:500;line-height:1.6;color:var(--vp-c-text-2);background:var(--vp-c-bg);cursor:pointer}
.primary-button{border-color:var(--lab-blue);background:var(--lab-blue);color:#fff}
.run-scroll{padding:16px 20px 22px;overflow:auto;min-height:0;flex:1;font-size:13px}
.data-field{margin:0 0 16px}.run-panel h4{margin:0 0 8px;padding:0;border:0;font-size:13px;font-weight:500;line-height:1.6;color:var(--vp-c-text-2)}
.run-panel pre,.question-input{display:block;width:100%;font:14px/1.8 var(--vp-font-family-mono);margin:0;padding:10px 13px;border:1px solid var(--vp-c-divider);border-radius:7px;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--vp-code-bg);color:var(--vp-c-text-1)}
.question-input{min-height:72px;resize:vertical}.question-input:focus-visible{outline:2px solid var(--lab-blue);outline-offset:1px}
.run-panel pre.live-text{margin-bottom:16px}.result-content>strong{display:block;font-size:16px;font-weight:600;margin:4px 0 17px}.passed{color:var(--lab-blue)}
.actual-output.pass pre{color:var(--lab-blue);background:var(--lab-blue-soft)}.actual-output.pass h4{color:var(--lab-blue)}.actual-output.fail pre{color:var(--lab-red);background:var(--lab-red-soft)}.actual-output.fail h4{color:var(--lab-red)}
.empty-result{margin:10px 0;font-size:14px;line-height:1.8;color:var(--vp-c-text-3)}
.job-status{display:grid;place-items:center;width:24px;height:32px;color:var(--vp-c-text-3)}.job-status svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;animation:agent-running-spin .8s linear infinite}@keyframes agent-running-spin{to{transform:rotate(360deg)}}
.stop-button{display:grid;place-items:center;width:32px;height:32px;padding:0;border:0;color:#868d97;background:transparent;cursor:pointer}.stop-button svg{width:20px;height:20px}.stop-button:hover{color:var(--vp-c-text-1)}
.approval-box{margin:12px 0 16px}.approval-box button{margin:10px 8px 0 0;padding:6px 10px;border:1px solid var(--vp-c-divider);border-radius:4px;color:var(--lab-blue);cursor:pointer}
.event-details{margin-top:20px;color:var(--vp-c-text-2)}.event-details summary{cursor:pointer;font-size:12px}.event-line{padding:9px 0;border-bottom:1px solid var(--vp-c-divider)}.event-line pre{margin:5px 0}
.run-panel button:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
@container(max-width:470px){.run-tabs{gap:5px;padding:6px 8px}.run-tabs>button{padding:5px;font-size:13px}.elapsed{display:none}.run-actions{gap:5px}.run-button,.primary-button{font-size:13px;padding:5px 8px}}
@media(max-width:600px){.run-scroll{padding:14px 15px 20px}.elapsed{display:none}}
</style>
