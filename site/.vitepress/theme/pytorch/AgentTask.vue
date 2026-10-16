<script setup lang="ts">
import rendered from 'virtual:agent-content';
import {computed} from 'vue';
import AgentCodeBlock from './AgentCodeBlock.vue';
const props=defineProps<{chapter:any}>();
const html=computed(()=>rendered[props.chapter.id]);
const spec=computed(()=>props.chapter.interface);
</script>
<template>
 <div class="agent-task">
  <div class="task-statement" v-html="html.task"/>
  <p class="task-target">在 <code>{{chapter.file}}</code> 中完成 <code>{{spec.function}}</code>。</p>
  <section class="question-section">
   <h3>输入与输出</h3>
   <ul class="interface-list">
    <li v-if="!spec.parameters.length">本函数不接收参数。</li>
    <li v-for="(parameter,i) in spec.parameters" :key="parameter.name"><code>{{parameter.name}}</code>：<code>{{parameter.type}}</code>。<span v-html="html.interface.parameters[i]"/></li>
    <li><strong>输出：</strong><span v-html="html.interface.returns"/></li>
   </ul>
  </section>
  <section class="question-section">
   <h3>编写要求</h3>
   <ol class="requirements"><li v-for="(requirement,i) in html.interface.requirements" :key="i" v-html="requirement"/></ol>
  </section>
  <section class="question-section example-case">
   <h3>示例</h3>
   <div class="example-body">
    <div class="example-line"><strong>输入：</strong><pre>{{spec.example.input}}</pre></div>
    <div class="example-line"><strong>输出：</strong><pre>{{spec.example.output}}</pre></div>
    <div class="example-line"><strong>解释：</strong><p v-html="html.interface.explanation"/></div>
   </div>
  </section>
  <section v-if="chapter.hints.length" class="question-section hints">
   <h3>提示</h3>
   <details v-for="(hint,i) in html.hints" :key="i" class="task-hint"><summary><span>提示 {{i+1}}</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><div class="hint-content" v-html="hint"/></details>
  </section>
  <details v-if="chapter.id!=='intro'" class="task-hint reference"><summary><span>参考实现</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><AgentCodeBlock :code="chapter.referenceCode"/></details>
 </div>
</template>
<style scoped>
.agent-task{font-size:15px;line-height:1.9;min-width:0}.task-statement :deep(p){margin:0 0 18px}.task-target{margin:0 0 6px;color:var(--vp-c-text-2);overflow-wrap:anywhere}
.agent-task :deep(code){padding:2px 5px;border-radius:4px;background:var(--vp-code-bg);color:var(--vp-c-text-2);font:13px/1.8 var(--vp-font-family-mono);overflow-wrap:anywhere}
.question-section{padding:22px 0}.agent-task .question-section h3{margin:0 0 15px;padding:0;border:0;font-size:16px;font-weight:600;line-height:1.6}
.interface-list,.requirements{padding-left:20px;margin:0}.interface-list li,.requirements li{margin:10px 0}.interface-list li:last-child{margin-top:14px}.interface-list li::marker,.requirements li::marker{color:var(--vp-c-text-3)}
.example-body{border-left:2px solid var(--vp-c-divider);padding-left:16px}.example-line{display:grid;grid-template-columns:52px minmax(0,1fr);gap:4px;margin-bottom:10px;line-height:1.85}.example-line:last-child{margin-bottom:0}
.agent-task .example-line pre{margin:0;padding:0;border:0;border-radius:0;background:transparent;color:var(--vp-c-text-2);font:14px/1.85 var(--vp-font-family-mono);white-space:pre-wrap;overflow-wrap:anywhere}.example-line p{margin:0;color:var(--vp-c-text-2)}
.agent-task .task-hint{margin:0 0 10px;padding:0;border:1px solid var(--vp-c-divider);border-radius:7px;background:var(--vp-c-bg);overflow:hidden}
.agent-task .task-hint summary{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0;padding:12px 15px;list-style:none;background:var(--vp-code-bg);color:var(--vp-c-text-2);font-size:13px;line-height:1.6;cursor:pointer}
.task-hint summary::-webkit-details-marker{display:none}.task-hint summary svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}.task-hint[open]>summary svg{transform:rotate(180deg)}
.task-hint summary:focus-visible{outline:2px solid var(--lab-blue);outline-offset:-2px}.agent-task .hint-content{padding:14px 15px;margin:0;font-size:14px}
.reference :deep(.agent-code){margin:0;border:0;border-top:1px solid var(--vp-c-divider);border-radius:0}
@media(max-width:600px){.example-body{padding-left:12px}.example-line{grid-template-columns:48px minmax(0,1fr)}.agent-task .example-line pre{font-size:12px}}
</style>
