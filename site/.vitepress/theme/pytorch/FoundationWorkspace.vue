<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue';
import {foundationTasks} from '../../../../exercises/foundations/tasks.mjs';
import FileWorkspaceEditor from './FileWorkspaceEditor.vue';
import PythonEditor from './PythonEditor.vue';
import AgentCodeBlock from './AgentCodeBlock.vue';
import DockerTerminal from './DockerTerminal.vue';
import WorkspaceDivider from './WorkspaceDivider.vue';
import {useFileWorkspaceLayout} from './file-workspace-layout';
import type {NavigationState} from './course-navigation';
import './agent-code.css';

const emit = defineEmits<{navigation:[state:NavigationState]}>();
const selected = ref(foundationTasks[0].id);
const task = computed(() => foundationTasks.find(entry=>entry.id===selected.value)!);
const siblings = computed(()=>foundationTasks.filter(entry=>entry.subject===task.value.subject));
const index = computed(()=>siblings.value.findIndex(entry=>entry.id===selected.value));
const filename = ref(task.value.entry);
const tab = ref<'task'|'example'>('task');
const drafts = ref<Record<string,Record<string,string>>>({});
const completed = ref<string[]>([]);
const terminals = ref<InstanceType<typeof DockerTerminal>[]>([]);
const learningScroll = ref<HTMLElement>();
const {splitter, codePane, split, bottomHeight, runExpanded, startSplit, dragSplit, stepSplit, startHeight, dragHeight, stepHeight} = useFileWorkspaceLayout();
const storageKey = 'development-foundations-v1';
const content = computed({
  get:()=>drafts.value[selected.value]?.[filename.value] ?? task.value.files[filename.value],
  set:(value:string)=>{
    if(!task.value.editable.includes(filename.value))return;
    drafts.value[selected.value] = {...drafts.value[selected.value],[filename.value]:value};
  },
});
function editedFiles(entry:any) {
  return Object.fromEntries(entry.editable.map((file:string)=>[file,drafts.value[entry.id]?.[file] ?? entry.files[file]]));
}
function selectTarget(id:string) {
  const next=foundationTasks.find(entry=>entry.id===id);
  if(!next)return false;
  selected.value=id; filename.value=next.entry; tab.value='task'; runExpanded.value=false;
  learningScroll.value?.scrollTo({top:0});
  return true;
}
function loadFile(name:string) {
  filename.value=name;
  terminals.value[foundationTasks.findIndex(entry=>entry.id===selected.value)]?.read(name);
}
function updateFile(id:string,name:string,value:string) {
  drafts.value[id]={...drafts.value[id],[name]:value};
}
function toggleComplete() {
  completed.value=completed.value.includes(selected.value)?completed.value.filter(id=>id!==selected.value):[...completed.value,selected.value];
}
onMounted(()=>{
  try{
    const saved=JSON.parse(localStorage.getItem(storageKey)||'null');
    for(const entry of foundationTasks)for(const file of Object.keys(entry.files)){
      if(typeof saved?.drafts?.[entry.id]?.[file]==='string')updateFile(entry.id,file,saved.drafts[entry.id][file]);
    }
    if(Array.isArray(saved?.completed))completed.value=foundationTasks.map(entry=>entry.id).filter(id=>saved.completed.includes(id));
  }catch{}
  emit('navigation',{selected:selected.value,completed:completed.value});
});
watch([drafts,completed],()=>{
  try{localStorage.setItem(storageKey,JSON.stringify({drafts:drafts.value,completed:completed.value}));}catch{}
},{deep:true});
watch([selected,completed],()=>emit('navigation',{selected:selected.value,completed:completed.value}));
defineExpose({selectTarget});
</script>
<template>
 <div class="agent-ide">
  <div ref="splitter" class="agent-panels" :style="{'--lesson-share':split+'fr','--editor-share':(1-split)+'fr'}">
   <section class="learning-pane">
    <header class="learning-tabs">
     <button type="button" :class="{active:tab==='task'}" @click="tab='task'">任务</button>
     <button type="button" :class="{active:tab==='example'}" @click="tab='example'">命令示例</button>
     <nav class="task-arrows" aria-label="切换关卡">
      <button aria-label="上一关" :disabled="index===0" @click="selectTarget(siblings[index-1].id)">‹</button>
      <span>{{index+1}} / {{siblings.length}}</span>
      <button aria-label="下一关" :disabled="index===siblings.length-1" @click="selectTarget(siblings[index+1].id)">›</button>
     </nav>
    </header>
    <article ref="learningScroll" class="learning-content">
     <h1>{{task.title}}</h1>
     <template v-if="tab==='task'">
      <p>{{task.goal}}</p>
      <p v-if="task.subject==='linux'">Windows 上终端使用 WSL 的默认 Linux 发行版，请先安装并完成 Ubuntu 的首次启动。</p>
      <h2>编写要求</h2>
      <ol><li v-for="item in task.requirements" :key="item">{{item}}</li></ol>
      <h2>验收结果</h2>
      <pre><code>{{task.expected}}</code></pre>
      <h2>验证指令：</h2>
      <AgentCodeBlock :code="task.commands"/>
      <details class="task-hint"><summary>提示</summary><p>{{task.hint}}</p></details>
      <button class="completion-button" :aria-pressed="completed.includes(selected)" @click="toggleComplete">{{completed.includes(selected)?'已完成 · 取消标记':'标记本关已完成'}}</button>
     </template>
     <template v-else>
      <h2>命令示例</h2>
      <p>先参考下面的命令，理解每一步的作用，再根据本关要求操作。</p>
      <AgentCodeBlock :code="task.example"/>
     </template>
    </article>
   </section>
   <WorkspaceDivider axis="x" label="调整学习区与代码区宽度" @start="startSplit" @drag="dragSplit" @step="stepSplit"/>
   <section ref="codePane" class="coding-pane">
    <FileWorkspaceEditor v-show="!runExpanded" :files="Object.keys(task.files)" :filename="filename" @select="loadFile">
     <PythonEditor v-model="content" :context-key="selected+':'+filename" :readonly="!task.editable.includes(filename)" language="text" :line-wrapping="true"/>
    </FileWorkspaceEditor>
    <WorkspaceDivider v-show="!runExpanded" axis="y" label="调整运行区高度" @start="startHeight" @drag="dragHeight" @step="stepHeight"/>
    <DockerTerminal v-for="entry in foundationTasks" v-show="entry.id===selected" ref="terminals" :key="entry.id" :task-id="entry.id" :files="editedFiles(entry)" :expanded="runExpanded" :style="{height:bottomHeight+'px'}" @expand="runExpanded=!runExpanded" @file="(name,value)=>updateFile(entry.id,name,value)"/>
   </section>
  </div>
 </div>
</template>
<style scoped src="./file-workspace.css"></style>
<style scoped>
.task-hint{margin:18px 0;padding:10px 14px;border:1px solid var(--vp-c-divider);border-radius:7px}
.task-hint summary{cursor:pointer;color:var(--vp-c-text-2)}
.completion-button{padding:5px 8px;border-radius:5px;color:var(--lab-blue);background:var(--lab-blue-soft);font-size:13px}
</style>
