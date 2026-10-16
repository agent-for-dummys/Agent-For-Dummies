<script setup lang="ts">
import {computed,onMounted,onUnmounted,onActivated,onDeactivated,ref,nextTick,watch} from 'vue';
import course from '../../../../oj/agent_course.json';
import rendered from 'virtual:agent-content';
import PythonEditor from './PythonEditor.vue';
import ProjectTree from './ProjectTree.vue';
import type {NavigationState} from './course-navigation';
import LocalStartGuide from './LocalStartGuide.vue';
import AgentHistory from './AgentHistory.vue';
import AgentRunPanel from './AgentRunPanel.vue';
import AgentTask from './AgentTask.vue';
import {request,exportAgentProject,isLocalSite,ApiError} from './api';
import './fonts.css';
import './agent-code.css';
const emit=defineEmits<{navigation:[state:NavigationState]}>();
const chapters=course.chapters;const selected=ref(chapters[0].id),tab=ref('learn');
const current=computed(()=>chapters.find(ch=>ch.id===selected.value)!);
const chapterIndex=computed(()=>chapters.findIndex(ch=>ch.id===selected.value));
const expandedFolders=ref<string[]>(['practice','mini_pi']),waiting=ref<any>();
const chapterResults=ref<Record<string,any>>({}),chapterEvents=ref<Record<string,any[]>>({});
const files=ref<Record<string,string>>({...course.files});const filename=ref(chapters[0].file),dirty=ref<string[]>([]),saving=ref(false),connected=ref(false),message=ref('');
const filesOpen=ref(false),active=ref(true),setupOpen=ref(false);
const completed=ref<string[]>([]),records=ref<any[]>([]),result=ref<any>(),events=ref<any[]>([]),busy=ref(false),status=ref(''),threadId=ref('main');
const inputDrafts=ref<Record<string,string>>({});
const question=computed({
 get:()=>inputDrafts.value[selected.value]??current.value.question,
 set:(value:string)=>{inputDrafts.value[selected.value]=value;try{localStorage.setItem('agent-course-v3-inputs',JSON.stringify(inputDrafts.value));}catch{}}
});
const panelTab=ref<'cases'|'result'>('cases'),runExpanded=ref(false);
const runQuestions=ref<Record<string,string>>({});
const codePane=ref<HTMLElement>(),bottomHeight=ref(240),resizeStart=ref<{y:number;height:number}>();
const isSubmission=(record:any)=>record.mode==='check'&&record.chapterId!=='intro';
const relevantRecords=computed(()=>records.value.filter(record=>isSubmission(record)&&record.chapterId===selected.value));
const splitter=ref<HTMLElement>(),split=ref(.5),splitStart=ref<{x:number;ratio:number}>();
const learningScroll=ref<HTMLElement>();
watch([selected,completed],()=>{if(active.value)emit('navigation',{selected:selected.value,completed:[...completed.value]});},{deep:true});
defineExpose({selectTarget:selectChapter});
let saveChain:Promise<boolean>=Promise.resolve(true);
const saveTimers=new Map<string,ReturnType<typeof setTimeout>>();
function scheduleSave(name:string){const pending=saveTimers.get(name);if(pending)clearTimeout(pending);saveTimers.set(name,setTimeout(()=>{saveTimers.delete(name);if(local)save(name);},700));}
const content=computed({get:()=>files.value[filename.value]||'',set:(value:string)=>{files.value[filename.value]=value;if(!dirty.value.includes(filename.value))dirty.value.push(filename.value);scheduleSave(filename.value);}});
const headings=computed(()=>Object.keys(files.value).filter(name=>name==='.env'||(current.value.phase==='foundation'?name.startsWith('practice/')&&chapters.slice(0,chapterIndex.value+1).some(ch=>(ch.referenceFiles||[ch.file]).includes(name)):!name.startsWith('practice/'))));
function toggleFolder(path:string){expandedFolders.value=expandedFolders.value.includes(path)?expandedFolders.value.filter(name=>name!==path):[...expandedFolders.value,path];}
function revealFile(name:string){const parts=name.split('/');for(let i=1;i<parts.length;i++){const folder=parts.slice(0,i).join('/');if(!expandedFolders.value.includes(folder))expandedFolders.value.push(folder);}}
let runController:AbortController|undefined;const local=isLocalSite();let jobId='';
async function loadFiles(){if(!local)return;try{const response=await request('/api/agent/files');for(const [name,value] of Object.entries(response.files))if(!dirty.value.includes(name))files.value[name]=value as string;connected.value=true;message.value='';}catch(error){connected.value=false;message.value=(error as Error).message;}}
async function save(name=filename.value){
 if(!dirty.value.includes(name))return true;
 if(!local){setupOpen.value=true;return false;}
 const snapshot=files.value[name];
 const operation=async()=>{
  if(files.value[name]!==snapshot)return true;
  saving.value=true;
  try{await request('/api/agent/files',{method:'POST',body:JSON.stringify({name,content:snapshot})});if(files.value[name]===snapshot)dirty.value=dirty.value.filter(n=>n!==name);message.value='';connected.value=true;return true;}
  catch(error){message.value=(error as Error).message;return false;}
  finally{saving.value=false;}
 };
 const pending=saveChain.then(operation);saveChain=pending.then(()=>true,()=>true);return pending;
}
async function saveAll(){for(const name of [...dirty.value])if(!await save(name))return false;return true;}
async function openFile(name:string){if(!await save())return;filename.value=name;revealFile(name);localStorage.setItem('agent-course-v3-file',name);}
async function selectChapter(id:string){if(!chapters.some(ch=>ch.id===id)||!await save())return false;selected.value=id;filename.value=current.value.file;nextTick(()=>learningScroll.value?.scrollTo({top:0}));revealFile(filename.value);tab.value='learn';panelTab.value='cases';runExpanded.value=false;localStorage.setItem('agent-course-v3-chapter',id);localStorage.setItem('agent-course-v3-file',filename.value);result.value=chapterResults.value[id]||(id==='project'?waiting.value:undefined);events.value=chapterEvents.value[id]||[];return true;}
function navigate(delta:number){const next=chapters[chapterIndex.value+delta];if(next)selectChapter(next.id);}
function editTask(){openFile(current.value.file);tab.value='task';}
async function copyLessonCode(event:MouseEvent){
 const button=(event.target as HTMLElement).closest<HTMLButtonElement>('.copy-code');
 const code=button?.parentElement?.querySelector('code')?.textContent;
 if(!button||code===undefined)return;
 const label=button.querySelector('span');
 try{await navigator.clipboard.writeText(code);if(label)label.textContent='已复制';}
 catch{if(label)label.textContent='复制失败';}
 setTimeout(()=>{if(label)label.textContent='复制';},1600);
}
async function download(){if(!local){setupOpen.value=true;return;}if(!await saveAll())return;try{const blob=await exportAgentProject();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='mini-pi.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){message.value=(error as Error).message;}}
async function poll(id:string,chapterId:string,mode:string,signal:AbortSignal,runThread=threadId.value){
 for(;;){
  let job;
  try{job=await request('/api/jobs/'+id,{},signal);}catch(error){if(error instanceof TypeError||error instanceof ApiError&&error.status>=500){status.value='queued';await new Promise(resolve=>setTimeout(resolve,1000));continue;}throw error;}
  status.value=job.status;chapterEvents.value[chapterId]=job.events||[];
  if(selected.value===chapterId)events.value=job.events||[];
  if(job.status==='done'){
   chapterResults.value[chapterId]=job.result;if(selected.value===chapterId)result.value=job.result;
   if(job.result.verdict==='WAITING'){waiting.value={...job.result,threadId:runThread};localStorage.setItem('agent-course-v3-waiting',JSON.stringify(waiting.value));threadId.value=runThread;}
   else if(chapterId==='project'&&mode==='live'){waiting.value=undefined;localStorage.removeItem('agent-course-v3-waiting');}
   if((mode!=='run'||chapterId==='intro')&&(job.result.verdict==='AC'||job.result.verdict==='OK')){if(!completed.value.includes(chapterId))completed.value.push(chapterId);localStorage.setItem('agent-course-v3-completed',JSON.stringify(completed.value));}
   if(mode==='check'&&chapterId!=='intro'&&!['SYSTEM','WAITING','CANCELLED'].includes(job.result.verdict)){records.value.unshift({chapterId,title:chapters.find(ch=>ch.id===chapterId)?.title,mode,at:Date.now(),result:job.result});records.value=records.value.slice(0,50);localStorage.setItem('agent-course-v3-records',JSON.stringify(records.value));}
   localStorage.removeItem('agent-course-v3-pending');await loadFiles();return;
  }
  await new Promise(resolve=>setTimeout(resolve,250));
 }
}
async function run(mode='check',approval?:boolean){
 if(busy.value)return;if(!local){setupOpen.value=true;return;}if(!await saveAll())return;
 const chapterId=selected.value,runThread=approval!==undefined&&waiting.value?waiting.value.threadId:threadId.value;
 runQuestions.value[chapterId]=question.value;
 const body=JSON.stringify({chapterId,mode,question:question.value,threadId:runThread,approval,requestId:crypto.randomUUID()});
 panelTab.value='result';busy.value=true;jobId='';result.value=undefined;events.value=[];message.value='';status.value='queued';runController=new AbortController();
 try{
  for(;;){try{const accepted=await request('/api/agent/jobs',{method:'POST',body},runController.signal);jobId=accepted.id;break;}catch(error){if(error instanceof TypeError||error instanceof ApiError&&error.status===503){status.value='queued';await new Promise(resolve=>setTimeout(resolve,1000));continue;}throw error;}}
  localStorage.setItem('agent-course-v3-pending',JSON.stringify({id:jobId,chapterId,mode,threadId:runThread,question:runQuestions.value[chapterId]}));
  await poll(jobId,chapterId,mode,runController.signal,runThread);
 }catch(error){if((error as Error).name!=='AbortError')message.value=(error as Error).message;}finally{busy.value=false;}
}
async function cancel(){if(!jobId){runController?.abort();return;}try{await request('/api/agent/jobs/'+jobId+'/cancel',{method:'POST'});}catch(error){message.value=(error as Error).message;}}
function resizeDown(event:PointerEvent){resizeStart.value={y:event.clientY,height:bottomHeight.value};(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);}
function resizeMove(event:PointerEvent){if(resizeStart.value)bottomHeight.value=Math.min((codePane.value?.clientHeight||700)-160,Math.max(42,resizeStart.value.height+resizeStart.value.y-event.clientY));}
function resizeEnd(){resizeStart.value=undefined;}
function splitMove(event:PointerEvent){if(splitStart.value)split.value=Math.min(.7,Math.max(.25,splitStart.value.ratio+(event.clientX-splitStart.value.x)/(splitter.value?.clientWidth||1000)));}
function keyboard(event:KeyboardEvent){if(!active.value)return;if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='s'){event.preventDefault();save();}}
function beforeUnload(event:BeforeUnloadEvent){if(dirty.value.length){event.preventDefault();event.returnValue='';}}
onMounted(async()=>{
 const saved=localStorage.getItem('agent-course-v3-chapter');if(chapters.some(ch=>ch.id===saved)){selected.value=saved!;filename.value=current.value.file;}
 try{const savedInputs=JSON.parse(localStorage.getItem('agent-course-v3-inputs')||'{}');if(savedInputs&&typeof savedInputs==='object'&&!Array.isArray(savedInputs))inputDrafts.value=Object.fromEntries(chapters.filter(ch=>typeof savedInputs[ch.id]==='string'&&savedInputs[ch.id].length<=4000).map(ch=>[ch.id,savedInputs[ch.id]]));}catch{}
 const savedFile=localStorage.getItem('agent-course-v3-file');if(savedFile&&savedFile in course.files)filename.value=savedFile;revealFile(filename.value);
 try{completed.value=JSON.parse(localStorage.getItem('agent-course-v3-completed')||'[]').filter((id:string)=>chapters.some(ch=>ch.id===id));records.value=JSON.parse(localStorage.getItem('agent-course-v3-records')||'[]').filter(isSubmission);localStorage.setItem('agent-course-v3-records',JSON.stringify(records.value));waiting.value=JSON.parse(localStorage.getItem('agent-course-v3-waiting')||'null');if(waiting.value){threadId.value=waiting.value.threadId;if(selected.value==='project')result.value=waiting.value;}}catch{}
 window.addEventListener('keydown',keyboard);window.addEventListener('beforeunload',beforeUnload);await loadFiles();
 const pending=localStorage.getItem('agent-course-v3-pending');if(pending&&local){try{const job=JSON.parse(pending);runQuestions.value[job.chapterId]=job.question??inputDrafts.value[job.chapterId]??chapters.find(ch=>ch.id===job.chapterId)?.question??'';panelTab.value='result';busy.value=true;jobId=job.id;runController=new AbortController();await poll(job.id,job.chapterId,job.mode,runController.signal,job.threadId);}catch(error){message.value=(error as Error).message;}finally{busy.value=false;}}
});
onActivated(()=>{active.value=true;emit('navigation',{selected:selected.value,completed:[...completed.value]});});onDeactivated(()=>{active.value=false;saveAll();});
onUnmounted(()=>{window.removeEventListener('keydown',keyboard);window.removeEventListener('beforeunload',beforeUnload);runController?.abort();for(const timer of saveTimers.values())clearTimeout(timer);});
</script>
<template>
 <div class="agent-ide">
  <LocalStartGuide :open="setupOpen" @close="setupOpen=false"/>
  <div ref="splitter" class="agent-panels" :style="{'--lesson-share':split+'fr','--editor-share':(1-split)+'fr'}">
   <section class="learning-pane">
    <header class="learning-tabs">
     <button type="button" :class="{active:tab==='learn'}" @click="tab='learn'">学习</button>
     <button type="button" :class="{active:tab==='task'}" @click="tab='task'">任务</button>
     <button type="button" :class="{active:tab==='records'}" @click="tab='records'">提交记录</button>
     <nav class="task-arrows" aria-label="切换任务"><button type="button" aria-label="上一任务" :disabled="chapterIndex===0" @click="navigate(-1)">‹</button><span>{{chapterIndex+1}} / {{chapters.length}}</span><button type="button" aria-label="下一任务" :disabled="chapterIndex===chapters.length-1" @click="navigate(1)">›</button></nav>
    </header>
    <article ref="learningScroll" class="learning-content">
     <h1>{{current.title}}</h1>
     <div v-if="tab==='learn'" class="lesson-prose" @click="copyLessonCode" v-html="rendered[current.id].lesson"/>
     <AgentTask v-else-if="tab==='task'" :key="current.id" :chapter="current"/>
     <AgentHistory v-else :key="selected" :records="relevantRecords"/>
    </article>
   </section>
   <div class="column-divider" role="separator" aria-label="调整学习区与代码区宽度" aria-orientation="vertical" tabindex="0" @pointerdown="splitStart={x:$event.clientX,ratio:split};($event.currentTarget as HTMLElement).setPointerCapture($event.pointerId)" @pointermove="splitMove" @pointerup="splitStart=undefined" @pointercancel="splitStart=undefined" @keydown.left.prevent="split=Math.max(.25,split-.03)" @keydown.right.prevent="split=Math.min(.7,split+.03)"><i/></div>
   <section ref="codePane" class="coding-pane">
    <div v-show="!runExpanded" class="editor-card">
     <header class="editor-toolbar">
      <button type="button" class="file-toggle" :aria-label="filesOpen?'收起文件栏':'展开文件栏'" :aria-expanded="filesOpen" @click="filesOpen=!filesOpen"><svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M2 5h6l2 2h8v10H2z" stroke="currentColor" stroke-linejoin="round"/><path d="M2 5V3h6l2 2" stroke="currentColor"/></svg></button>
      <span class="editor-filename" :title="filename">{{filename.split('/').pop()}}</span><span v-if="dirty.includes(filename)" class="dirty-dot" aria-label="正在保存">•</span>
      <button v-if="current.phase==='project'" type="button" class="export-button" title="导出自己的项目" @click="download">导出</button>
     </header>
     <div class="editor-body">
      <aside v-if="filesOpen" class="file-explorer" aria-label="项目文件"><ProjectTree :files="headings" :selected="filename" :expanded="expandedFolders" @select="openFile" @toggle="toggleFolder"/></aside>
      <div class="code-surface"><PythonEditor v-model="content" :context-key="'agent-v3:'+filename" :language="filename.endsWith('.py')?'python':'text'" :line-wrapping="true" focus-marker="TODO" @run="run(current.live?'live':'run')"/></div>
     </div>
    </div>
    <div v-show="!runExpanded" class="output-divider" role="separator" aria-label="调整运行区高度" aria-orientation="horizontal" tabindex="0" @pointerdown="resizeDown" @pointermove="resizeMove" @pointerup="resizeEnd" @pointercancel="resizeEnd" @keydown.down.prevent="bottomHeight=Math.max(48,bottomHeight-25)" @keydown.up.prevent="bottomHeight=Math.min((codePane?.clientHeight||700)-160,bottomHeight+25)"><i/></div>
    <AgentRunPanel v-model:question="question" v-model:tab="panelTab" :run-question="runQuestions[selected]" :chapter="current" :expanded="runExpanded" :busy="busy" :status="status" :message="message" :result="result" :events="events" :style="{height:bottomHeight+'px'}" @expand="runExpanded=!runExpanded" @run="run" @cancel="cancel"/>
   </section>
  </div>
 </div>
</template>
<style scoped>
.agent-ide {
 --vp-c-bg:#fff;--vp-c-bg-alt:#fff;--vp-c-bg-soft:#f3f8fd;
 --vp-c-divider:#e5eaf0;--vp-c-border:#d7dfe8;--vp-code-bg:#f7f9fc;
 --vp-c-text-1:#252b36;--vp-c-text-2:#596579;--vp-c-text-3:#78869a;
 --lab-blue:#0087be;--lab-blue-soft:#edf7ff;--lab-selection:#dcedfb;
 --lab-red:#bd4955;--lab-red-soft:#fff1f2;
 height:calc(100dvh - 120px);min-height:560px;font-size:14px;color:var(--vp-c-text-1);
}
.dark .agent-ide{--vp-c-bg:#1b2028;--vp-c-bg-alt:#1b2028;--vp-c-bg-soft:#242d38;--vp-c-divider:#343d49;--vp-c-border:#465365;--vp-code-bg:#252b34;--vp-c-text-1:#e4e9f0;--vp-c-text-2:#b4becd;--vp-c-text-3:#94a2b6;--lab-blue:#78c6f2;--lab-blue-soft:#20374a;--lab-selection:#334d67}
.agent-panels{height:100%;display:grid;grid-template-columns:minmax(0,var(--lesson-share)) 8px minmax(0,var(--editor-share));min-height:0}
.learning-pane,.coding-pane{display:flex;flex-direction:column;min-width:0;min-height:0}
.learning-pane,.editor-card{border:1px solid var(--vp-c-divider);border-radius:10px;overflow:hidden;background:var(--vp-c-bg)}
.learning-tabs,.editor-toolbar{display:flex;align-items:center;gap:5px;min-height:48px;padding:6px 10px;border-bottom:1px solid var(--vp-c-divider);flex:none}
.learning-tabs>button{padding:5px 8px;border:0;border-radius:5px;font-size:14px;font-weight:500;color:var(--vp-c-text-2);white-space:nowrap}
.learning-tabs>button.active{color:var(--lab-blue);background:var(--lab-blue-soft)}
.task-arrows{display:flex;align-items:center;gap:6px;margin-left:auto;color:var(--vp-c-text-3);font:11px var(--vp-font-family-mono)}
.task-arrows button{font-size:22px;color:var(--lab-blue);width:22px}.task-arrows button:disabled{opacity:.3}
.learning-content{overflow:auto;flex:1;padding:28px 30px;line-height:1.95;min-height:0}
.learning-content h1{font-size:25px;line-height:1.5;margin:0 0 25px;font-weight:650}
.learning-content h2,.learning-content :deep(h3){font-size:17px;margin:28px 0 15px;padding:0;border:0;font-weight:600}
.lesson-prose :deep(p){margin:0 0 18px}.lesson-prose :deep(a){color:var(--lab-blue)}
.learning-content :deep(code){font-family:var(--vp-font-family-mono);font-size:.9em;background:var(--vp-code-bg);color:var(--vp-c-text-2);padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}
.learning-content :deep(pre){font:13px/1.85 var(--vp-font-family-mono);white-space:pre-wrap;overflow-wrap:anywhere;word-break:normal;tab-size:4;max-width:100%;margin:16px 0}
.learning-content :deep(pre){padding:17px 18px;border:1px solid var(--vp-c-divider);border-radius:6px;background:var(--vp-code-bg)}
.learning-content :deep(pre:not(.shiki) code){display:block;width:auto;min-width:0;max-width:100%;padding:0;border:0;background:transparent;color:var(--vp-c-text-1);font-size:inherit;white-space:pre-wrap;overflow-wrap:anywhere}
.learning-content :deep(ul),.learning-content :deep(ol){padding-left:20px}.learning-content :deep(li){margin:8px 0}
.success-example{color:var(--vp-c-text-2);margin-bottom:24px}.success-example :deep(p){margin:0}
.task-hint{border-top:1px solid var(--vp-c-divider);padding:12px 0}.task-hint summary{cursor:pointer;font-size:13px;color:var(--vp-c-text-2)}.task-hint>div{margin-top:12px}.task-hint.reference pre{margin-bottom:0}
.column-divider{display:flex;align-items:center;justify-content:center;cursor:col-resize;touch-action:none}.column-divider i{height:36px;width:2px;background:var(--vp-c-border);border-radius:2px}
.editor-card{display:flex;flex-direction:column;flex:1;min-height:150px}.editor-toolbar{gap:9px}.file-toggle{display:flex;align-items:center;justify-content:center;width:24px;height:28px;color:var(--vp-c-text-2)}
.editor-filename{font:12px var(--vp-font-family-mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dirty-dot{font-size:12px;color:var(--vp-c-text-3)}.export-button{margin-left:auto;font-size:12px;color:var(--vp-c-text-2);padding:5px}
.editor-body{display:flex;flex:1;min-height:0;position:relative}.file-explorer{flex:none;width:170px;overflow:auto;background:var(--vp-code-bg);padding:10px 6px;border-right:1px solid var(--vp-c-divider)}.code-surface{flex:1;min-width:0;min-height:0}.code-surface :deep(.cm-gutters){background:var(--vp-c-bg)}
.output-divider{height:8px;flex:none;display:flex;align-items:center;justify-content:center;cursor:row-resize;touch-action:none}.output-divider i{width:32px;height:2px;background:var(--vp-c-border);border-radius:2px}
.dark .agent-ide{--lab-red:#f18b96;--lab-red-soft:#3c282e}
.agent-ide :deep(*){scrollbar-color:#d0d3d6 transparent;scrollbar-width:thin}.agent-ide :deep(*::-webkit-scrollbar){width:6px;height:6px}.agent-ide :deep(*::-webkit-scrollbar-thumb){background:#d0d3d6;border-radius:6px}.agent-ide :deep(*::-webkit-scrollbar-track){background:transparent}
@media(max-width:850px){.learning-content{padding:23px}.file-explorer{position:absolute;inset:0 auto 0 0;z-index:5;width:190px;box-shadow:4px 0 15px #00000012}.learning-tabs>button{font-size:12px}}
@media(max-width:600px){.agent-ide{height:auto;min-height:0}.agent-panels{display:flex;flex-direction:column;gap:10px}.learning-pane{height:65dvh;min-height:400px}.coding-pane{height:75dvh;min-height:550px}.column-divider{display:none}.learning-content{padding:22px}.learning-content h1{font-size:23px}.learning-content :deep(pre){padding:13px;font-size:12px}}
</style>
