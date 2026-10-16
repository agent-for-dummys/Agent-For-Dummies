<script setup lang="ts">
import {computed,ref} from 'vue';
import ErrorFeedback from './ErrorFeedback.vue';
import {verdictLabels as labels} from './verdicts';

type RunRecord={at:number;mode:string;chapterId:string;output?:string;result:{verdict:string;elapsedMs?:number;message?:string;stdout?:string;cases?:{name:string;status:string;message?:string}[]}};
const props=defineProps<{records:RunRecord[]}>();
const expanded=ref<number>();
const current=computed(()=>props.records.find(record=>record.at===expanded.value)||props.records[0]);
const passed=(record:RunRecord)=>['AC','OK'].includes(record.result.verdict);
const count=(record:RunRecord)=>record.result.cases?.filter(item=>item.status==='passed').length||0;
const label=(record:RunRecord)=>labels[record.result.verdict]||record.result.verdict;
</script>

<template>
 <div class="agent-history">
  <p v-if="!current" class="empty-history">还没有提交记录。</p>
  <template v-else>
   <div class="submission-summary" :class="{accepted:passed(current)}">
    <span class="status-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path :d="passed(current)?'M4 10l4 4 8-8':'M6 6l8 8M14 6l-8 8'" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
    <div>
     <strong class="submission-title">{{label(current)}}</strong>
     <div class="submission-count"><time>{{new Date(current.at).toLocaleString('zh-CN')}}</time><span v-if="current.result.cases?.length">{{count(current)}} / {{current.result.cases.length}} tests passed</span><span v-if="current.result.elapsedMs!==undefined">{{current.result.elapsedMs}} ms</span></div>
    </div>
   </div>
   <h2 class="content-label">提交记录</h2>
   <div class="history-table">
    <article v-for="record in records" :key="record.at" class="history-card" :class="{selected:record.at===current.at}">
     <button type="button" class="history-row" :aria-expanded="expanded===record.at" @click="expanded=expanded===record.at?undefined:record.at">
      <span class="history-mode">提交</span>
      <time>{{new Date(record.at).toLocaleString('zh-CN')}}</time>
      <span class="status-badge" :class="passed(record)?'pass':'fail'">{{label(record)}}</span>
      <svg class="history-chevron" :class="{expanded:expanded===record.at}" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>
     </button>
     <div v-if="expanded===record.at" class="history-details">
      <div v-if="record.result.cases?.length||record.result.elapsedMs!==undefined" class="history-metrics"><span v-if="record.result.cases?.length">{{count(record)}} / {{record.result.cases.length}} tests passed</span><span v-if="record.result.elapsedMs!==undefined">执行时间：{{record.result.elapsedMs}} ms</span></div>
      <ErrorFeedback v-if="!passed(record)" :verdict="record.result.verdict" :message="record.result.message"/>
      <div v-for="item in record.result.cases" :key="item.name" class="history-case"><span>{{item.name}}</span><span :class="item.status==='passed'?'pass':'fail'">{{item.status==='passed'?'Passed':'Failed'}}</span><ErrorFeedback v-if="item.message" verdict="WA" :message="item.message" :show-type="false"/></div>
      <pre v-if="record.output||record.result.stdout" class="history-output">{{record.output||record.result.stdout}}</pre>
     </div>
    </article>
   </div>
  </template>
 </div>
</template>

<style scoped>
.agent-history{font-variant-numeric:tabular-nums lining-nums}
.submission-summary{display:flex;align-items:center;gap:14px;margin:0 0 24px;padding:20px;border:1px solid var(--vp-c-divider);border-radius:9px;background:var(--vp-c-bg)}
.submission-summary.accepted{border-color:#c6e2f7;background:var(--lab-blue-soft)}
.status-icon{display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;border-radius:50%;color:var(--lab-red);background:var(--lab-red-soft)}
.accepted .status-icon{color:var(--lab-blue);background:var(--lab-blue-soft)}
.submission-title{display:block;font-size:22px;line-height:1.5;font-weight:600;color:var(--vp-c-text-1)}
.accepted .submission-title{color:var(--lab-blue)}
.submission-count{display:flex;align-items:center;flex-wrap:wrap;column-gap:8px;margin-top:8px;color:var(--vp-c-text-2);font-size:13px;line-height:1.9}
.submission-count>span:before{content:'·';margin-right:8px}
.agent-history .content-label{margin:0 0 14px;padding:0;border:0;font-size:16px;font-weight:600;line-height:1.6}
.history-table{display:grid;gap:12px}
.history-card{border:1px solid var(--vp-c-divider);border-radius:9px;background:var(--vp-c-bg);overflow:hidden}
.history-card.selected{border-color:#c6e2f7}
.history-row{display:flex;align-items:center;flex-wrap:wrap;gap:12px;width:100%;min-height:58px;padding:15px 16px;border:0;background:transparent;font:13px/1.6 var(--vp-font-family-base);color:var(--vp-c-text-1);text-align:left;cursor:pointer}
.history-row:hover{background:var(--vp-code-bg)}
.history-row:focus-visible{outline:2px solid var(--lab-blue);outline-offset:-2px;border-radius:8px}
.history-row time{margin-right:auto;font-size:12px;color:var(--vp-c-text-3);white-space:nowrap}
.status-badge{width:fit-content;padding:3px 8px;border-radius:4px;font-size:13px;font-weight:500;line-height:1.6;white-space:nowrap}
.status-badge.pass{background:var(--lab-blue-soft)}
.status-badge.fail{background:var(--lab-red-soft)}
.pass{color:var(--lab-blue)}.fail{color:var(--lab-red)}
.history-chevron{width:16px;height:16px;flex-shrink:0;fill:none;stroke:var(--vp-c-text-3);stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.history-chevron.expanded{transform:rotate(180deg)}
.history-details{padding:0 16px 16px}
.history-metrics{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 14px;font-size:12px;color:var(--vp-c-text-2)}
.history-case{display:flex;align-items:center;flex-wrap:wrap;gap:10px;padding:10px 0;border-bottom:1px solid var(--vp-c-divider);font-size:13px}
.history-case>span:first-child{flex:1}.history-case .error-feedback{width:100%;margin:0}
.agent-history pre.history-output{margin:14px 0 0;padding:14px;border:1px solid var(--vp-c-divider);border-radius:7px;background:var(--vp-c-bg);font:13px/1.85 var(--vp-font-family-mono);white-space:pre-wrap;overflow-wrap:anywhere}
.empty-history{font-size:14px;color:var(--vp-c-text-2)}
.dark .submission-summary.accepted,.dark .history-card.selected{border-color:#3c647f}
</style>
