<script setup lang="ts">
import { computed } from 'vue';
import rendered from 'virtual:pytorch-content';
import LevelDot from './LevelDot.vue';
import { pythonValue,outputText } from './format';
interface Task {id:string;title:string;level:string;parameters:{name:string;type:string;description:string}[];returns:string;examples:{input:unknown;output:unknown;explanation?:string}[];outputNames?:string[]}
const props=defineProps<{problem:Task;solved?:boolean;compact?:boolean}>();
const html=computed(()=>rendered.problems[props.problem.id]);
function exampleInput(input:unknown){
 const parts=props.problem.parameters.map((p,i)=>`${p.name} = ${pythonValue((input as unknown[])[i])}`);
 return parts.every(p=>!p.includes('\n'))&&parts.join(', ').length<=100?parts.join(', '):parts.join('\n');
}
</script>
<template>
 <article class="question-content" :class="{compact}">
  <header class="question-heading"><LevelDot :level="problem.level"/><h2>{{ problem.title }}</h2><span v-if="solved" class="answered" aria-label="Accepted">✓</span></header>
  <section class="question-section statement"><div class="rich-content" v-html="html.statement"/><div v-if="html.formula" class="rich-content" v-html="html.formula"/></section>
  <section class="question-section interface"><h3>输入与输出</h3><ul class="interface-list"><li v-for="(p,i) in problem.parameters" :key="p.name"><code>{{ p.name }}</code>：<span v-html="html.parameters[i]"/></li><li><strong>输出</strong>：<span v-html="html.returns"/></li></ul></section>
  <section class="question-section examples"><article v-for="(example,i) in problem.examples" :key="i" class="example-case"><h4>示例 {{ i+1 }}：</h4><div class="example-body"><div class="example-line"><strong>输入：</strong><pre>{{ exampleInput(example.input) }}</pre></div><div class="example-line"><strong>输出：</strong><pre>{{ outputText(example.output,problem) }}</pre></div><div v-if="example.explanation" class="example-line"><strong>解释：</strong><p v-html="html.explanations[i]"/></div></div></article></section>
  <section class="question-section"><h3>数据范围</h3><ul class="limits"><li v-for="(line,i) in html.limits" :key="i" v-html="line"/></ul></section>
 </article>
</template>
<style scoped>
.question-heading{display:flex;align-items:center;gap:11px;margin-bottom:20px}.question-heading h2{font-size:23px;line-height:1.5;font-weight:600;letter-spacing:-.3px;border:0;padding:0;margin:0}.compact .question-heading h2{font-size:19px}.answered{margin-left:auto;color:var(--lab-blue);font-size:15px}
.question-section{padding:22px 0}.question-section.statement{padding-top:0}.question-section h3{font-size:16px;font-weight:600;margin:0 0 15px;line-height:1.6}
.rich-content{font-size:15px;line-height:1.9}.rich-content :deep(p){font-size:15px;line-height:1.9;margin:15px 0}.rich-content :deep(code),.interface-list code,.limits :deep(code){font-size:13px;padding:2px 4px;border-radius:3px;color:var(--vp-code-color);background:var(--vp-code-bg)}.rich-content :deep(mjx-container){max-width:100%;overflow-x:auto;overflow-y:hidden;font-size:100%!important}.rich-content :deep(mjx-container[jax="SVG"]>svg){max-width:none}.rich-content :deep(mjx-assistive-mml){overflow:hidden}
.interface-list{padding-left:20px;margin:0;font-size:15px;line-height:1.9}.interface-list li{margin:10px 0}.interface-list li:last-child{margin-top:14px}.interface-list strong{font-weight:600}.interface-list li::marker{color:var(--vp-c-text-3)}
.example-case{margin:0 0 25px}.example-case:last-child{margin-bottom:0}.example-case h4{font-size:15px;font-weight:600;line-height:1.6;margin:0 0 14px}.example-body{border-left:2px solid var(--vp-c-divider);padding-left:16px}.example-line{display:grid;grid-template-columns:52px minmax(0,1fr);font-size:15px;line-height:1.85}.example-line strong{font-size:15px;font-weight:600}.example-line pre{display:block;font:14px/1.85 var(--vp-font-family-mono);color:var(--vp-c-text-2);white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:0;border:0;background:transparent}.example-line p{font-size:15px;line-height:1.85;color:var(--vp-c-text-2);margin:0}
.limits{padding-left:20px;margin:0;font-size:15px;line-height:1.9}.limits li{margin-top:10px}.limits li::marker{color:var(--vp-c-text-3)}
.question-heading h2{min-width:0;overflow-wrap:anywhere}
.interface-list :deep(code){font:13px var(--vp-font-family-mono);padding:2px 5px;border:1px solid var(--vp-c-divider);border-radius:4px;background:var(--vp-code-bg);color:var(--vp-code-color)}
.example-line p :deep(code){font:13px/1.85 var(--vp-font-family-mono);padding:2px 4px;border-radius:3px;background:var(--vp-code-bg);color:var(--vp-code-color)}
@media(max-width:600px){.question-heading h2{font-size:21px}.example-body{padding-left:12px}.example-line{grid-template-columns:48px minmax(0,1fr)}}
</style>
