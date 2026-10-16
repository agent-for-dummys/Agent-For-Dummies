<script setup lang="ts">
import {computed,nextTick,ref,watch} from 'vue';
const props=defineProps<{open:boolean;course:any;selected:string;completed:string[]}>();
const emit=defineEmits<{close:[];select:[id:string];switch:[track:'pytorch'|'agent']}>();
const dialog=ref<HTMLDialogElement>();
const search=ref('');
const expanded=ref<string[]>([props.course.groups[0]]);
const groups=computed(()=>props.course.groups.map((title:string)=>({title,chapters:props.course.chapters.filter((chapter:any)=>chapter.group===title&&(!search.value||chapter.title.toLowerCase().includes(search.value.toLowerCase())))})).filter((group:any)=>group.chapters.length));
watch(()=>props.open,async value=>{await nextTick();if(value){const group=props.course.chapters.find((ch:any)=>ch.id===props.selected)?.group;if(group&&!expanded.value.includes(group))expanded.value.push(group);if(!dialog.value?.open)dialog.value?.showModal();}else dialog.value?.close();});
function toggle(title:string){expanded.value=expanded.value.includes(title)?expanded.value.filter(item=>item!==title):[...expanded.value,title];}
function backdrop(event:MouseEvent){if(event.target!==dialog.value)return;const rect=dialog.value!.getBoundingClientRect();if(event.clientX>rect.right||event.clientY>rect.bottom)emit('close');}
</script>
<template>
 <dialog ref="dialog" class="agent-catalog" aria-labelledby="agent-catalog-title" @cancel.prevent="emit('close')" @click="backdrop">
  <header><strong id="agent-catalog-title">题目列表</strong><button type="button" aria-label="关闭题目列表" @click="emit('close')">×</button></header>
  <nav class="catalog-switch" aria-label="切换学习课程"><button type="button" @click="emit('switch','pytorch')">PyTorch 入门</button><button type="button" class="active" aria-pressed="true">Agent 从 0 到 1</button></nav>
  <div class="catalog-search"><input v-model="search" aria-label="搜索任务" placeholder="搜索任务 / 函数"/></div>
  <div class="catalog-list"><section v-for="group in groups" :key="group.title" class="catalog-group">
   <button type="button" class="group-title" :aria-expanded="expanded.includes(group.title)||!!search" @click="toggle(group.title)"><span class="group-toggle">{{expanded.includes(group.title)||search?'−':'+'}}</span><span>{{group.title}}</span><small>{{group.chapters.filter((chapter:any)=>completed.includes(chapter.id)).length}}/{{group.chapters.length}}</small></button>
   <div v-if="expanded.includes(group.title)||search" class="group-items"><button v-for="chapter in group.chapters" :key="chapter.id" type="button" :class="{active:chapter.id===selected}" @click="emit('select',chapter.id)"><span class="completion" :class="{done:completed.includes(chapter.id)}">{{completed.includes(chapter.id)?'✓':'○'}}</span><span>{{chapter.title}}</span></button></div>
  </section><p v-if="!groups.length">没有找到匹配内容。</p></div>
 </dialog>
</template>
<style scoped>
.agent-catalog{position:fixed;inset:0 auto 0 0;width:min(360px,90vw);height:100dvh;max-height:100dvh;max-width:100vw;margin:0;padding:0;border:0;border-right:1px solid var(--vp-c-divider);border-radius:0;background:var(--vp-c-bg);color:var(--vp-c-text-1);box-shadow:8px 0 28px #00000024;display:flex;flex-direction:column}.agent-catalog:not([open]){display:none}.agent-catalog::backdrop{background:#15253640}header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--vp-c-divider);flex:none}header strong{font-size:17px;font-weight:600}header button{width:28px;height:28px;font-size:24px;color:var(--vp-c-text-2)}.catalog-switch{display:flex;gap:3px;padding:4px;margin:14px 18px 0;background:var(--vp-code-bg);border-radius:7px;flex:none}.catalog-switch button{flex:1;padding:7px 3px;font-size:12px;border-radius:4px;color:var(--vp-c-text-2)}.catalog-switch .active{background:var(--vp-c-bg);color:var(--lab-blue);box-shadow:0 1px 3px #00000010}.catalog-search{padding:16px 18px 10px}.catalog-search input{width:100%;padding:9px 11px;border:1px solid var(--vp-c-border);border-radius:6px;background:var(--vp-c-bg);font-size:13px;outline:none}.catalog-search input:focus{border-color:var(--lab-blue)}.catalog-list{flex:1;overflow:auto;padding:0 18px 20px;scrollbar-color:#d0d3d6 transparent;scrollbar-width:thin}.catalog-group{margin:8px 0 16px;border:1px solid var(--vp-c-divider);border-radius:8px;overflow:hidden}.group-title{display:flex;align-items:center;gap:8px;width:100%;padding:13px 12px;text-align:left;background:var(--vp-code-bg);font-size:14px;font-weight:600}.group-toggle{color:var(--vp-c-text-3);width:10px;flex:none}.group-title small{margin-left:auto;font:11px var(--vp-font-family-mono);color:var(--vp-c-text-3)}.group-items>button{display:flex;align-items:center;gap:10px;padding:12px;width:100%;border-top:1px solid var(--vp-c-divider);text-align:left;font-size:12px;color:var(--vp-c-text-2)}.group-items>button.active{background:var(--lab-blue-soft);color:var(--lab-blue)}.completion{width:16px;color:var(--vp-c-text-3)}.completion.done{color:var(--lab-blue)}.catalog-list>p{font-size:13px;color:var(--vp-c-text-3)}
</style>
