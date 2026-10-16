<script setup lang="ts">
import {verdictLabels as labels} from './verdicts';
import { computed, nextTick, onMounted, onUnmounted, onActivated, onDeactivated, ref, watch } from 'vue';
import rendered from 'virtual:pytorch-content';
import PythonEditor from './PythonEditor.vue';
import RunPanel from './RunPanel.vue';
import ProblemContent from './ProblemContent.vue';
import ErrorFeedback from './ErrorFeedback.vue';
import LevelDot from './LevelDot.vue';
import PaneExpandButton from './PaneExpandButton.vue';
import PaneBookmark from './PaneBookmark.vue';
import './fonts.css';
import { pythonValue, inputText as formatInput, outputText as formatOutput } from './format';
import { health, judge, pollJob, isLocalSite, type Health, type JudgeResult } from './api';
import LocalStartGuide from './LocalStartGuide.vue';
import type {NavigationState} from './course-navigation';

type View = 'lesson' | 'problem' | 'solution' | 'history';
type Level = '入门' | '简单' | '中等' | '困难';
interface Lesson { name:string; signature:string; description:string; code:string; url:string; output:string; input:string; practices:string[] }
interface Module { id:string; title:string; level:Level; lessons:Lesson[] }
interface Problem {
 id:string; moduleId:string; title:string; level:Level; signature:string; statement:string; constraints:string[]; kind?:string;parentId?:string;lessonKey?:string;
 parameters:{name:string;type:string;description:string}[]; returns:string; ranges:string[];
 starter:string; solution:string; analysis:string[]; outputNames?:string[];
 examples:{input:unknown;output:unknown;explanation?:string}[]; visibleTests:number; totalTests:number;
}
interface Submission { id?:string;problemId:string; verdict:string; passed:number; total:number; at:number; code?:string; result?:JudgeResult }
const props=defineProps<{track:'pytorch'|'agent';course:any}>();
const emit=defineEmits<{navigation:[state:NavigationState]}>();
const course=props.course as {version:number;title?:string;modules:Module[];problems:Problem[]};
const track=props.track;
const storageKey='pytorch-course-v1';
const mainProblems=course.modules.flatMap(m=>course.problems.filter(p=>p.moduleId===m.id&&(!p.kind||p.kind==='problem')));
const practiceId=ref<string>();
const learningScroll=ref<HTMLElement>();
const scrollToStart=()=>nextTick(()=>learningScroll.value?.scrollTo({top:0}));
const activeModule=ref(course.modules[0].id), problemId=ref(course.problems[0].id), lessonIndex=ref(0), view=ref<View>('lesson');
const drafts=ref<Record<string,string>>({}), solved=ref<string[]>([]), history=ref<Submission[]>([]);
const selectedRecord=ref<number>(), resultCode=ref<Record<string,string>>({}), results=ref<Record<string,JudgeResult>>({});
const connection=ref<Health>(), connectionError=ref(''), checking=ref(false), busy=ref(false), jobStatus=ref(''), activeJobKey=ref('');
const activeJobCode=ref('');
const localSite=ref(false),showStartGuide=ref(false);
const labReady=ref(false);
const pendingRun=ref<{id:string;contextKey:string;problemId:string;kind:'example'|'run'|'submit';code:string}>();
const inputText=(input:unknown)=>formatInput(input,problem.value);
const outputText=(value:unknown)=>formatOutput(value,problem.value);
const exampleInputText=(input:unknown)=>{
 const parts=problem.value.parameters.map((p,i)=>`${p.name} = ${pythonValue((input as unknown[])[i])}`);
 return parts.every(p=>!p.includes('\n'))&&parts.join(', ').length<=100?parts.join(', '):parts.join('\n');
};
const panelTab=ref<'cases'|'result'>('cases'),panelRatio=ref(.38),codingPane=ref<HTMLElement>(),codingHeight=ref(0),resizing=ref(false),copied=ref(false),copyError=ref(false);
const panelCollapsed=ref(false),runHeaderHeight=ref(46);
const expandedPane=ref<'learning'|'editor'|'tests'|null>(null),splitRatio=ref(.5),workArea=ref<HTMLElement>(),workWidth=ref(0),columnResizing=ref(false);
const hiddenSide=ref<'learning'|'coding'|null>(null),collapseTarget=ref<'learning'|'coding'|null>(null),columnHandle=ref<HTMLElement>();
const activeHiddenSide=computed(()=>expandedPane.value?null:hiddenSide.value);
const splitMin=computed(()=>Math.min(.5,320/Math.max(640,workWidth.value-8)));
const splitMax=computed(()=>1-splitMin.value);
const effectiveSplit=computed(()=>Math.min(splitMax.value,Math.max(splitMin.value,splitRatio.value)));
const workStyle=computed(()=>expandedPane.value?undefined:activeHiddenSide.value?{gridTemplateColumns:activeHiddenSide.value==='learning'?'28px minmax(0,1fr)':'minmax(0,1fr) 28px'}:{gridTemplateColumns:`minmax(0,${effectiveSplit.value}fr) 8px minmax(0,${1-effectiveSplit.value}fr)`});
let workObserver:ResizeObserver|undefined,columnDrag:{id:number;x:number;ratio:number;width:number}|undefined;
function setSplitRatio(value:number){splitRatio.value=Math.min(splitMax.value,Math.max(splitMin.value,value));}
function startColumnResize(event:PointerEvent){if(event.button!==0)return;event.preventDefault();columnDrag={id:event.pointerId,x:event.clientX,ratio:effectiveSplit.value,width:Math.max(1,workWidth.value-8)};columnResizing.value=true;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);}
function updateColumnResize(event:PointerEvent){
 if(columnDrag?.id!==event.pointerId)return;
 const bounds=workArea.value!.getBoundingClientRect();
 collapseTarget.value=event.clientX<=bounds.left+40?'learning':event.clientX>=bounds.right-40?'coding':null;
 setSplitRatio(columnDrag.ratio+(event.clientX-columnDrag.x)/columnDrag.width);
}
function endColumnResize(){columnDrag=undefined;columnResizing.value=false;collapseTarget.value=null;}
function finishColumnResize(event:PointerEvent){
 if(columnDrag?.id!==event.pointerId)return;
 updateColumnResize(event);
 if(collapseTarget.value){hiddenSide.value=collapseTarget.value;splitRatio.value=columnDrag.ratio;}
 endColumnResize();
}
function restoreSide(){hiddenSide.value=null;nextTick(()=>columnHandle.value?.focus({preventScroll:true}));}
function resizeColumnsWithKeyboard(event:KeyboardEvent){if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();setSplitRatio(effectiveSplit.value+(event.key==='ArrowLeft'?-.03:.03));}else if(event.key==='Home'||event.key==='End'){event.preventDefault();hiddenSide.value=event.key==='Home'?'learning':'coding';}}
function togglePane(pane:NonNullable<typeof expandedPane.value>){endPanelResize();endColumnResize();expandedPane.value=expandedPane.value===pane?null:pane;}
function restoreLayout(event:KeyboardEvent){if(event.key==='Escape'){if(expandedPane.value)expandedPane.value=null;else if(hiddenSide.value)restoreSide();}}
const panelMin=computed(()=>Math.ceil(runHeaderHeight.value)+2);
const panelMax=computed(()=>Math.max(panelMin.value,codingHeight.value-200));
const panelHeight=computed(()=>panelCollapsed.value?panelMin.value:Math.min(panelMax.value,Math.max(panelMin.value,(codingHeight.value||720)*panelRatio.value)));
let panelObserver:ResizeObserver|undefined,drag:{id:number;y:number;height:number;ratio:number}|undefined,copyTimer:ReturnType<typeof setTimeout>|undefined;
function setPanelHeight(height:number){
 const bounded=Math.min(panelMax.value,Math.max(panelMin.value,height));
 if(bounded<=panelMin.value+1){if(!panelCollapsed.value&&drag)panelRatio.value=drag.ratio;panelCollapsed.value=true;}
 else{panelCollapsed.value=false;panelRatio.value=bounded/(codingHeight.value||720);}
}
function revealPanel(){if(panelCollapsed.value){panelCollapsed.value=false;panelRatio.value=Math.max(.25,panelRatio.value);}}
function resetPanelSize(){panelCollapsed.value=false;panelRatio.value=.38;}
function startPanelResize(event:PointerEvent){if(event.button!==0)return;event.preventDefault();drag={id:event.pointerId,y:event.clientY,height:panelHeight.value,ratio:panelRatio.value};resizing.value=true;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);}
function updatePanelResize(event:PointerEvent){if(drag?.id===event.pointerId)setPanelHeight(drag.height+drag.y-event.clientY);}
function endPanelResize(){drag=undefined;resizing.value=false;}
function resizeWithKeyboard(event:KeyboardEvent){const amount={ArrowUp:24,ArrowDown:-24}[event.key];if(amount){event.preventDefault();setPanelHeight(panelHeight.value+amount);}else if(event.key==='Home'||event.key==='End'){event.preventDefault();setPanelHeight(event.key==='Home'?panelMin.value:panelMax.value);}}
async function copySolution(){clearTimeout(copyTimer);try{await navigator.clipboard.writeText(problem.value.solution);copied.value=true;copyError.value=false;}catch{copyError.value=true;}copyTimer=setTimeout(()=>{copied.value=false;copyError.value=false;},2000);}
let mounted=false, controller:AbortController|undefined, healthController:AbortController|undefined;
const module=computed(()=>course.modules.find(m=>m.id===activeModule.value)!);
const mainProblem=computed(()=>course.problems.find(p=>p.id===problemId.value)!);
const mainBase=computed(()=>mainProblem.value.parentId?course.problems.find(p=>p.id===mainProblem.value.parentId)!:mainProblem.value);
const problem=computed(()=>practiceId.value?course.problems.find(p=>p.id===practiceId.value)!:mainProblem.value);
const problemIndex=computed(()=>mainProblems.findIndex(p=>p.id===mainBase.value.id));
const lesson=computed(()=>module.value.lessons[lessonIndex.value]||module.value.lessons[0]);
const lessonMode=computed(()=>view.value==='lesson');
const exampleMode=computed(()=>lessonMode.value&&!practiceId.value);
const functionContext=computed(()=>lessonMode.value||!!practiceId.value);
const functionPractices=computed(()=>(lesson.value.practices||[]).map(id=>course.problems.find(p=>p.id===id)!));
const relatedVariations=computed(()=>course.problems.filter(p=>p.kind==='variation'&&p.parentId===mainBase.value.id));
const lessonHtml=computed(()=>rendered.lessons[`${module.value.id}:${lessonIndex.value}`]);
const problemHtml=computed(()=>rendered.problems[problem.value.id]);
const key=computed(()=>exampleMode.value?`lesson:${module.value.id}:${lessonIndex.value}`:problem.value.id);
const initialCode=computed(()=>exampleMode.value?lesson.value.code:problem.value.starter);
const code=computed({get:()=>drafts.value[key.value]??initialCode.value,set:value=>drafts.value={...drafts.value,[key.value]:value}});
const result=computed(()=>results.value[key.value]);
const pending=computed(()=>busy.value&&activeJobKey.value===key.value);
const runLabel=computed(()=>pending.value?jobStatus.value==='connecting'?'连接中…':jobStatus.value==='queued'?'排队中…':'运行中…':exampleMode.value?'运行示例':'运行');
const engineLabel=computed(()=>connection.value?.ready?`${track==='agent'?'LangGraph':'PyTorch'} ${connection.value.version} · ${track==='agent'?'本地':'CPU'}`:checking.value?'连接中':'未连接');
watch(key,()=>{panelTab.value='cases';copied.value=false;copyError.value=false;});
const relevantHistory=computed(()=>history.value.filter(h=>h.problemId===problem.value.id));
const record=computed(()=>relevantHistory.value.find(h=>h.at===selectedRecord.value)||relevantHistory.value[0]);
const failures=computed(()=>record.value?.result?.cases.filter(c=>c.status!=='passed')||[]);
const failedCaseIndex=ref(0);
const failedCase=computed(()=>failures.value[failedCaseIndex.value]||failures.value[0]);
watch(record,()=>failedCaseIndex.value=0);

const groupProblems=(id:string)=>mainProblems.filter(p=>p.moduleId===id);
const isPass=(verdict:string)=>verdict==='AC';
function chooseModule(id:string){practiceId.value=undefined;if(activeModule.value!==id){problemId.value=groupProblems(id)[0].id;lessonIndex.value=0;}activeModule.value=id;view.value='lesson';selectedRecord.value=undefined;scrollToStart();}
function chooseProblem(p:Problem){practiceId.value=undefined;if(activeModule.value!==p.moduleId)lessonIndex.value=0;activeModule.value=p.moduleId;problemId.value=p.id;view.value='problem';selectedRecord.value=undefined;scrollToStart();}
function choosePractice(id?:string){practiceId.value=id;view.value='lesson';selectedRecord.value=undefined;scrollToStart();}
function changeView(next:View){if(next==='problem')practiceId.value=undefined;view.value=next;scrollToStart();}
function moveProblem(delta:number){const target=mainProblems[problemIndex.value+delta];if(target)chooseProblem(target);}
function moveLesson(delta:number){const next=lessonIndex.value+delta;if(!module.value.lessons[next])return;practiceId.value=undefined;lessonIndex.value=next;view.value='lesson';scrollToStart();}
function navigate(delta:number){if(functionContext.value)moveLesson(delta);else moveProblem(delta);}
function notifyNavigation(){emit('navigation',{selected:functionContext.value?'module:'+activeModule.value:mainBase.value.id,completed:[...solved.value]});}
watch([activeModule,functionContext,mainBase,solved],notifyNavigation,{deep:true});
defineExpose({selectTarget:(id:string)=>{
 if(id.startsWith('module:')){const moduleId=id.slice(7);if(!course.modules.some(module=>module.id===moduleId))return false;chooseModule(moduleId);}
 else{const target=course.problems.find(problem=>problem.id===id);if(!target)return false;chooseProblem(target);}
 return true;
}});
const navigationIndex=computed(()=>functionContext.value?lessonIndex.value:problemIndex.value);
const navigationCount=computed(()=>functionContext.value?module.value.lessons.length:mainProblems.length);
function remember(id:string,data:JudgeResult,capturedCode:string,jobId?:string){
 if(data.verdict==='SYSTEM')return;
 const item={id:jobId,problemId:id,verdict:data.verdict,passed:data.passed||0,total:data.total||0,at:Date.now(),code:capturedCode,result:data};
 history.value=[item,...history.value.filter(h=>!jobId||h.id!==jobId)].slice(0,50);
 if(data.verdict==='AC'&&!solved.value.includes(id))solved.value=[...solved.value,id];
 if(problem.value.id===id){selectedRecord.value=item.at;view.value='history';scrollToStart();}
}
function save(){
 if(!mounted)return;
 try{localStorage.setItem(storageKey,JSON.stringify({version:course.version,drafts:drafts.value,solved:solved.value,history:history.value.slice(0,50),pendingRun:pendingRun.value,panelRatio:panelRatio.value,panelCollapsed:panelCollapsed.value,splitRatio:splitRatio.value,hiddenSide:hiddenSide.value,location:{module:activeModule.value,lesson:lessonIndex.value,problem:problemId.value,practice:practiceId.value,view:view.value}}));}catch{}
}
async function resumeRun(){
 const job=pendingRun.value;if(!job)return;
 const requestController=new AbortController();controller=requestController;
 busy.value=true;activeJobKey.value=job.contextKey;activeJobCode.value=job.code;jobStatus.value='queued';if(key.value===job.contextKey)panelTab.value='result';
 try{const data=await pollJob(job.id,status=>jobStatus.value=status,requestController.signal);results.value={...results.value,[job.contextKey]:data};resultCode.value={...resultCode.value,[job.contextKey]:job.code};if(job.kind==='submit')remember(job.problemId,data,job.code,job.id);}
 catch(error){if(error instanceof Error&&error.name!=='AbortError')connectionError.value=error.message;}
 finally{busy.value=false;jobStatus.value='';if(!requestController.signal.aborted){pendingRun.value=undefined;save();}}
}

async function checkConnection(){
 checking.value=true;connectionError.value='';healthController?.abort();const requestController=new AbortController();healthController=requestController;const timeout=setTimeout(()=>requestController.abort(),7000);
 try{const value=await health(requestController.signal);if(healthController===requestController){const engine=value.engines?.[track];connection.value=engine?{...value,...engine}:value;if(!connection.value.ready)connectionError.value=value.message||'请运行 npm run setup 安装本地课程依赖。';}}
 catch(error){if(healthController===requestController){connection.value=undefined;connectionError.value=error instanceof TypeError?'暂时无法连接判题服务。':error instanceof Error&&error.name!=='AbortError'?error.message:'暂时无法连接判题服务。';}}
 finally{clearTimeout(timeout);if(healthController===requestController)checking.value=false;}
}
async function execute(kind:'run'|'submit'){
 if(busy.value)return;
 // Capture before any await: health checks and editor updates must not change this job.
 const contextKey=key.value,id=problem.value.id,mode=exampleMode.value?'example':kind,capturedCode=code.value;
 if(!localSite.value){showStartGuide.value=true;return;}
 revealPanel();panelTab.value='result';busy.value=true;activeJobKey.value=contextKey;activeJobCode.value=capturedCode;jobStatus.value='connecting';
 const requestController=new AbortController();controller=requestController;
 let acceptedJobId:string|undefined;
 try{
  if(!connection.value?.ready){await checkConnection();if(!connection.value?.ready||requestController.signal.aborted)return;}
  jobStatus.value='queued';
  const data=await judge({kind:mode,track,problemId:mode==='example'?undefined:id,taskKey:contextKey,code:capturedCode},status=>jobStatus.value=status,requestController.signal,jobId=>{acceptedJobId=jobId;pendingRun.value={id:jobId,contextKey,problemId:id,kind:mode,code:capturedCode};save();});
  results.value={...results.value,[contextKey]:data};resultCode.value={...resultCode.value,[contextKey]:capturedCode};
  if(mode==='submit')remember(id,data,capturedCode,acceptedJobId);
 }catch(error){
  if(error instanceof Error&&error.name==='AbortError')return;
  const data:JudgeResult={verdict:'SYSTEM',message:error instanceof TypeError?'暂时无法连接判题服务。':error instanceof Error?error.message:'运行失败。',cases:[]};
  results.value={...results.value,[contextKey]:data};resultCode.value={...resultCode.value,[contextKey]:capturedCode};
 }finally{busy.value=false;jobStatus.value='';controller=undefined;if(!requestController.signal.aborted){pendingRun.value=undefined;save();}}
}
watch([drafts,solved,history,panelRatio,panelCollapsed,splitRatio,hiddenSide,activeModule,lessonIndex,problemId,practiceId,view],()=>save(),{deep:true});
onMounted(()=>{
 try{
  const data=JSON.parse(localStorage.getItem(storageKey)||'null');
  if(data?.version===course.version){
   if(typeof data.panelRatio==='number'&&data.panelRatio>=.01&&data.panelRatio<=.85)panelRatio.value=data.panelRatio;
   panelCollapsed.value=data.panelCollapsed===true;
   if(typeof data.splitRatio==='number'&&data.splitRatio>=.15&&data.splitRatio<=.85)splitRatio.value=data.splitRatio;
   if(data.hiddenSide==='learning'||data.hiddenSide==='coding')hiddenSide.value=data.hiddenSide;
   drafts.value=Object.fromEntries(Object.entries(data.drafts||{}).filter(([k,v])=>(course.problems.some(p=>p.id===k)||/^lesson:[a-z-]+:\d+$/.test(k))&&typeof v==='string'&&v.length<=20000)) as Record<string,string>;
   solved.value=(data.solved||[]).filter((id:string)=>course.problems.some(p=>p.id===id));
   history.value=(data.history||[]).filter((h:any)=>course.problems.some(p=>p.id===h.problemId)&&typeof h.at==='number'&&h.verdict!=='SYSTEM').slice(0,50);
   if(data.pendingRun&&typeof data.pendingRun.id==='string'&&/^[\w-]{16,64}$/.test(data.pendingRun.id)&&typeof data.pendingRun.code==='string'&&data.pendingRun.code.length<=20000&&['example','run','submit'].includes(data.pendingRun.kind))pendingRun.value=data.pendingRun;
   const location=data.location,current=course.modules.find(m=>m.id===location?.module);
   if(current){
    activeModule.value=current.id;
    lessonIndex.value=Number.isInteger(location.lesson)&&location.lesson>=0&&location.lesson<current.lessons.length?location.lesson:0;
    problemId.value=course.problems.find(p=>p.id===location.problem&&p.moduleId===current.id&&p.kind!=='practice')?.id||groupProblems(current.id)[0].id;
    if(['lesson','problem','solution','history'].includes(location.view))view.value=location.view;
    const savedPractice=course.problems.find(p=>p.id===location.practice&&p.lessonKey===`${current.id}:${lessonIndex.value}`&&lesson.value.practices.includes(p.id));
    if(savedPractice&&view.value!=='problem')practiceId.value=savedPractice.id;
   }
  }
 }catch{}
 if(codingPane.value){panelObserver=new ResizeObserver(entries=>codingHeight.value=entries[0].contentRect.height);panelObserver.observe(codingPane.value);}
 if(workArea.value){workObserver=new ResizeObserver(entries=>workWidth.value=entries[0].contentRect.width);workObserver.observe(workArea.value);}
 document.addEventListener('keydown',restoreLayout);
 mounted=true;localSite.value=isLocalSite();if(localSite.value){checkConnection();if(pendingRun.value)resumeRun();}
});
onUnmounted(()=>{mounted=false;controller?.abort();healthController?.abort();panelObserver?.disconnect();workObserver?.disconnect();document.removeEventListener('keydown',restoreLayout);clearTimeout(copyTimer);endPanelResize();endColumnResize();});
onActivated(()=>{document.addEventListener('keydown',restoreLayout);notifyNavigation();});
onDeactivated(()=>{document.removeEventListener('keydown',restoreLayout);});
</script>

<template>
 <div class="pytorch-lab" :data-course="track" :aria-busy="!labReady">
  <div v-if="!labReady" class="lab-loading" role="status">正在准备学习界面…</div>
  <LocalStartGuide :open="showStartGuide" @close="showStartGuide=false"/>
  <div class="lab-grid" :class="{'column-resizing':columnResizing,'preparing':!labReady}">
   <div ref="workArea" class="work-area" :class="{'single-pane':!!expandedPane,'side-collapsed':!!activeHiddenSide,'left-collapsed':activeHiddenSide==='learning','right-collapsed':activeHiddenSide==='coding','collapse-left-target':collapseTarget==='learning','collapse-right-target':collapseTarget==='coding'}" :style="workStyle">
   <PaneBookmark v-if="activeHiddenSide==='learning'" side="left" label="题目" @restore="restoreSide"/>
   <section v-show="activeHiddenSide!=='learning'&&(!expandedPane||expandedPane==='learning')" class="learning-pane" aria-label="函数讲解与题目">
    <nav class="learning-tabs" aria-label="学习内容">
     <button v-for="tab in [{id:'lesson',name:'函数学习'},{id:'problem',name:'题目描述'},{id:'solution',name:'题解'},{id:'history',name:'提交记录'}]" :key="tab.id" type="button" :class="{active:view===tab.id}" @click="changeView(tab.id as View)">{{ tab.name }}</button>
     <span class="problem-navigation"><button type="button" :disabled="navigationIndex===0" :aria-label="functionContext?'上一个函数':'上一题'" :title="functionContext?'上一个函数':'上一题'" @click="navigate(-1)">‹</button><span>{{ navigationIndex+1 }} / {{ navigationCount }}</span><button type="button" :disabled="navigationIndex===navigationCount-1" :aria-label="functionContext?'下一个函数':'下一题'" :title="functionContext?'下一个函数':'下一题'" @click="navigate(1)">›</button></span>
     <PaneExpandButton :expanded="expandedPane==='learning'" label="题目区" @toggle="togglePane('learning')"/>
    </nav>
    <div ref="learningScroll" class="learning-scroll">
     <template v-if="view==='lesson'">
      <h2 class="pane-title">{{ lesson.name }}</h2>
      <div class="lesson-steps" aria-label="调用示例与函数练习"><button type="button" :class="{active:!practiceId}" :aria-pressed="!practiceId" @click="choosePractice()">调用示例</button><button v-for="(p,i) in functionPractices" :key="p.id" type="button" :class="{active:practiceId===p.id}" :aria-pressed="practiceId===p.id" @click="choosePractice(p.id)">练习 {{ i+1 }}</button></div>
      <template v-if="!practiceId"><article class="function-detail"><pre class="function-signature">{{ lesson.signature }}</pre><div class="rich-content" v-html="lessonHtml"/><a :href="lesson.url" target="_blank" rel="noopener noreferrer">官方文档 ↗</a></article></template>
      <ProblemContent v-else :problem="problem" :solved="solved.includes(problem.id)" compact/>

      <div v-if="lessonIndex===module.lessons.length-1" class="lesson-next"><p>接下来可以开始本章练习。</p><button type="button" @click="chooseProblem(groupProblems(module.id)[0])">开始本章练习 →</button></div>
     </template>
     <template v-else-if="view==='problem'">
      <div class="variant-switch" aria-label="原题与变式"><button type="button" :class="{active:problem.id===mainBase.id}" @click="chooseProblem(mainBase)">原题</button><button v-for="(p,i) in relatedVariations" :key="p.id" type="button" :class="{active:problem.id===p.id}" @click="chooseProblem(p)">变式题<span v-if="solved.includes(p.id)"> ✓</span></button></div>
      <ProblemContent :problem="problem" :solved="solved.includes(problem.id)"/>

     </template>
     <template v-else-if="view==='solution'">
      <h2 class="pane-title">{{ problem.id }}. {{ problem.title }}</h2><h3 class="content-label">解题思路</h3><ol class="analysis-list"><li v-for="(html,i) in problemHtml.analysis" :key="i"><div class="rich-content" v-html="html"/></li></ol><h3 class="content-label">代码</h3><div class="solution-block"><button type="button" class="copy-solution" :aria-label="copied?'代码已复制':'复制题解代码'" @click="copySolution"><svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="7" y="6" width="9" height="11" rx="1.5" stroke="currentColor"/><path d="M12 6V3H3v11h4" stroke="currentColor"/></svg>{{ copied?'已复制':copyError?'复制失败':'复制' }}</button><pre class="solution-code">{{ problem.solution }}</pre></div>
     </template>
     <template v-else>
      <h2 class="pane-title">{{ problem.id }}. {{ problem.title }}</h2><p v-if="!relevantHistory.length" class="empty-history">还没有提交记录。</p>
      <template v-else><div class="submission-summary" :class="{accepted:isPass(record!.verdict)}"><span class="status-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path :d="isPass(record!.verdict)?'M4 10l4 4 8-8':'M6 6l8 8M14 6l-8 8'" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><div><strong class="submission-title">{{ labels[record!.verdict]||record!.verdict }}</strong><span class="submission-count"><time>{{ new Date(record!.at).toLocaleString('zh-CN') }}</time><span> · </span><template v-if="record!.total">{{ record!.passed }} / {{ record!.total }} tests passed</template><template v-else>Not tested</template><span v-if="record!.result?.elapsedMs!==undefined"> · {{ record!.result.elapsedMs }} ms</span></span></div></div><ErrorFeedback v-if="record!.result?.message&&!failedCase" :verdict="record!.verdict" :message="record!.result.message" :line="record!.result.line"/>
       <section v-if="failedCase" class="failed-case">
        <header class="failure-heading"><h3>失败用例</h3><select v-model="failedCaseIndex" aria-label="选择失败用例"><option v-for="(test,i) in failures" :key="i" :value="i">{{ test.name }}</option></select></header>
        <ErrorFeedback :verdict="record!.verdict" :message="failedCase.message" :line="failedCase.line"/>
        <template v-if="failedCase.input!==undefined"><span class="example-label">输入：</span><pre>{{ inputText(failedCase.input) }}</pre></template>
        <template v-if="failedCase.expected!==undefined"><span class="example-label">期望输出：</span><pre>{{ outputText(failedCase.expected) }}</pre></template>
        <template v-if="failedCase.actual!==undefined"><span class="example-label">实际输出：</span><pre>{{ outputText(failedCase.actual) }}</pre></template><p v-else class="case-error">没有返回结果。</p>
       </section>
       <pre v-if="record!.result?.stdout" class="stdout">{{ record!.result.stdout }}</pre>
       <p v-if="!record!.result" class="empty-history">此旧记录未保存用例详情。</p>
       <h3 class="content-label">提交记录</h3><div class="history-table"><article v-for="item in relevantHistory" :key="item.at" class="history-card" :class="{selected:item.at===record!.at}"><button type="button" class="history-row" :aria-expanded="selectedRecord===item.at" @click="selectedRecord=selectedRecord===item.at?undefined:item.at"><span class="history-language">Python</span><time>{{ new Date(item.at).toLocaleString('zh-CN') }}</time><span :class="['status-badge',isPass(item.verdict)?'pass':'fail']">{{ labels[item.verdict]||item.verdict }}</span><span aria-hidden="true" class="history-chevron">{{ selectedRecord===item.at?'⌃':'⌄' }}</span></button><div v-if="selectedRecord===item.at" class="history-details"><div class="history-metrics"><span>{{ item.passed }} / {{ item.total }} tests passed</span><span v-if="item.result?.elapsedMs!==undefined">执行时间：{{ item.result.elapsedMs }} ms</span></div><pre v-if="item.code!==undefined" class="solution-code">{{ item.code }}</pre><p v-else class="empty-history">此旧记录未保存代码。</p></div></article></div>
      </template>
     </template>
    </div>
   </section>
   <div v-show="!expandedPane&&!activeHiddenSide" ref="columnHandle" class="column-divider" role="separator" aria-label="调整题目区与代码区宽度" title="拖到两侧边缘收起，双击恢复默认宽度" aria-orientation="vertical" :aria-valuemin="Math.round(splitMin*100)" :aria-valuemax="Math.round(splitMax*100)" :aria-valuenow="Math.round(effectiveSplit*100)" tabindex="0" @pointerdown="startColumnResize" @pointermove="updateColumnResize" @pointerup="finishColumnResize" @pointercancel="endColumnResize" @lostpointercapture="endColumnResize" @keydown="resizeColumnsWithKeyboard" @dblclick="splitRatio=.5"><i/></div>
   <section v-show="activeHiddenSide!=='coding'&&expandedPane!=='learning'" ref="codingPane" class="coding-pane" :class="{resizing,'expanded-editor':expandedPane==='editor','expanded-tests':expandedPane==='tests'}" aria-label="Python 编程与判题">
    <div v-show="expandedPane!=='tests'" class="editor-card">
    <header class="editor-top"><span>{{ exampleMode?'调用示例':'Python 代码' }}</span><span v-if="localSite" class="engine-state" :class="{online:connection?.ready}"><i/>{{ engineLabel }}</span><button v-if="localSite" type="button" class="small-action" title="重新检查判题环境" aria-label="重新检查判题环境" @click="checkConnection">↻</button><button type="button" class="small-action" @click="code=initialCode">重置</button><template v-if="expandedPane==='editor'"><button type="button" class="small-action" @click="togglePane('tests')">{{ panelTab==='result'?'运行结果':'测试用例' }}</button><button type="button" :disabled="busy" class="run-button" @click="execute('run')">{{ runLabel }}</button><button v-if="!exampleMode" type="button" :disabled="busy" class="submit-button" @click="execute('submit')">提交</button></template><PaneExpandButton :expanded="expandedPane==='editor'" label="代码区" @toggle="togglePane('editor')"/></header>
    <div class="main-editor"><PythonEditor :context-key="key" v-model="code" @run="execute('run')" @ready="labReady=true"/></div>
    </div>

    <div v-show="!expandedPane" class="panel-divider" role="separator" aria-label="调整代码区与运行区大小" aria-orientation="horizontal" :aria-valuemin="panelMin" :aria-valuemax="Math.round(panelMax)" :aria-valuenow="Math.round(panelHeight)" tabindex="0" @pointerdown="startPanelResize" @pointermove="updatePanelResize" @pointerup="endPanelResize" @pointercancel="endPanelResize" @lostpointercapture="endPanelResize" @keydown="resizeWithKeyboard" @dblclick="resetPanelSize"><i/></div>
    <RunPanel v-show="expandedPane!=='editor'" v-model:tab="panelTab" :expanded="expandedPane==='tests'" :collapsed="panelCollapsed&&expandedPane!=='tests'" :style="expandedPane==='tests'?{height:'100%',flex:'1'}:{height:`${panelHeight}px`,flexBasis:`${panelHeight}px`}" :problem="problem" :lesson="lesson" :lesson-mode="exampleMode" :context-key="key" :result="result" :pending="pending" :job-status="jobStatus" :connection-error="connectionError" @retry="checkConnection" @expand="togglePane('tests')" @reveal="revealPanel" @header-height="runHeaderHeight=$event"><template #actions><button type="button" :disabled="busy" class="run-button" title="运行当前代码" @click="execute('run')">{{ runLabel }}</button><button v-if="!exampleMode" type="button" :disabled="busy" class="submit-button" @click="execute('submit')">提交</button></template></RunPanel>

   </section>
   <PaneBookmark v-if="activeHiddenSide==='coding'" side="right" label="代码" @restore="restoreSide"/>
   </div>
  </div>
 </div>
</template>


<style scoped>
.lab-grid.preparing{visibility:hidden}.lab-loading{position:absolute;padding:25px;font-size:14px;color:var(--vp-c-text-2)}
.pytorch-lab {
 --vp-c-bg:#fff; --vp-c-bg-alt:#fff; --vp-c-bg-soft:#f3f8fd;
 --vp-c-divider:#e5eaf0; --vp-c-border:#d7dfe8;
 --vp-code-bg:#f7f9fc; --vp-code-color:#334155;
 --vp-c-text-1:#252b36; --vp-c-text-2:#596579; --vp-c-text-3:#78869a;
 --lab-blue:#087fbd; --lab-blue-soft:#edf6fd; --lab-red:#bd4955; --lab-red-soft:#fff1f2;
 --lab-board:#f5f7f9;
 color:var(--vp-c-text-1); font-size:15px; font-weight:400;
}
:global(.dark .pytorch-lab) {
 --vp-c-bg:#1b1e24; --vp-c-bg-alt:#1b1e24; --vp-c-bg-soft:#232f3d;
 --vp-c-divider:#343d49; --vp-c-border:#465365;
 --vp-code-bg:#252b34; --vp-code-color:#d4dce8;
 --vp-c-text-1:#e4e9f0; --vp-c-text-2:#b4becd; --vp-c-text-3:#94a2b6;
 --lab-blue:#78c6f2; --lab-blue-soft:#20374a; --lab-red:#f18b96; --lab-red-soft:#3c282e;
 --lab-board:#14181f;
}
.lab-grid { display:grid; grid-template-columns:minmax(0,1fr); height:calc(100dvh - 120px); min-height:560px; background:var(--lab-board); }
.work-area { display:grid; min-width:0; min-height:0; }
.work-area.single-pane { grid-template-columns:minmax(0,1fr); }
.work-area.side-collapsed { gap:8px; }
.collapse-left-target .learning-pane,.collapse-right-target .coding-pane { opacity:.55; }
.collapse-left-target .column-divider i,.collapse-right-target .column-divider i { background:var(--lab-blue); }
.learning-pane,.coding-pane { display:flex; flex-direction:column; min-width:0; min-height:0; }
.learning-pane,.editor-card,.run-panel { border:1px solid var(--vp-c-divider); border-radius:10px; overflow:hidden; background:var(--vp-c-bg); }
.learning-pane { container-type:inline-size; }
.learning-tabs { display:flex; align-items:center; flex-wrap:wrap; gap:5px; min-height:48px; padding:6px 10px; border-bottom:1px solid var(--vp-c-divider); background:var(--vp-c-bg); flex-shrink:0; }
.learning-tabs>button { padding:5px 8px; font-size:14px; font-weight:500; color:var(--vp-c-text-2); border:0; border-radius:5px; white-space:nowrap; }
.learning-tabs>button.active { color:var(--lab-blue); background:var(--lab-blue-soft); }
.problem-navigation { display:flex; align-items:center; gap:3px; margin-left:auto; color:var(--vp-c-text-2); font-size:12px; white-space:nowrap; }
.problem-navigation button { font-size:24px; font-weight:500; line-height:30px; width:24px; height:30px; border-radius:4px; color:var(--lab-blue); }
.problem-navigation button:hover:not(:disabled) { background:var(--lab-blue-soft); }
.problem-navigation button:disabled { opacity:.25; }
.learning-scroll { padding:22px 24px 30px; overflow:auto; flex:1; min-height:0; }
.column-divider { display:flex; align-items:center; justify-content:center; min-width:0; cursor:col-resize; touch-action:none; outline:none; }
.column-divider i { width:2px; height:36px; border-radius:2px; background:var(--vp-c-border); }
.column-divider:hover i,.column-divider:focus-visible i,.column-resizing .column-divider i { background:var(--lab-blue); }
.column-divider:focus-visible { outline:2px solid var(--lab-blue); outline-offset:-2px; border-radius:4px; }
.column-resizing { user-select:none; cursor:col-resize; }
.coding-pane { container-type:inline-size; }
.editor-card { display:flex; flex-direction:column; flex:1; min-height:180px; min-width:0; }
.editor-card { overflow:visible; }.editor-top { border-radius:10px 10px 0 0; }.main-editor { border-radius:0 0 10px 10px; }
.expanded-editor .editor-card { height:100%; }
.expanded-tests .run-panel { min-height:0; }
@container(max-width:470px) { .problem-navigation>span { display:none; }.learning-tabs { gap:2px; padding:6px; }.learning-tabs>button { font-size:13px; padding:5px 6px; }.learning-scroll { padding:22px 20px 30px; } }
@container(max-width:390px) { .learning-tabs { column-gap:0; }.problem-navigation { margin-left:auto; } }
@container(max-width:470px) { .editor-top { flex-wrap:wrap; padding:8px 10px; gap:6px; }.engine-state { font-size:10px; }.editor-top>span:first-child { font-size:13px; } }
.pytorch-lab h2.pane-title { border:0; padding:0; font-size:23px; font-weight:600; line-height:1.5; margin:0 0 18px; letter-spacing:-.3px; }
.pytorch-lab .function-signature { background:var(--vp-code-bg); border:0; border-radius:4px; color:var(--vp-code-color); padding:11px 13px; margin:16px 0; white-space:pre-wrap; overflow-wrap:anywhere; font:13px/1.85 var(--vp-font-family-mono); }
.function-detail a { font-size:14px; color:var(--lab-blue); }
.lesson-next { margin-top:26px; padding-top:18px; }
.pytorch-lab .lesson-next p { margin:0 0 12px; font-size:15px; color:var(--vp-c-text-2); }
.lesson-next button,.load-solution { padding:8px 11px; border:1px solid var(--vp-c-border); border-radius:4px; font-size:14px; font-weight:500; color:var(--lab-blue); }
.rich-content { font-size:15px; line-height:1.9; }
.rich-content :deep(p) { margin:15px 0; font-size:15px; line-height:1.9; }
.rich-content :deep(h3) { font-size:15px; font-weight:600; margin:24px 0 12px; }
.rich-content :deep(ul) { padding-left:20px; margin:9px 0; }
.rich-content :deep(li) { margin:10px 0; font-size:15px; line-height:1.85; }
.rich-content :deep(code) { font-size:13px; background:var(--vp-code-bg); color:var(--vp-code-color); border-radius:3px; padding:2px 4px; }
.rich-content :deep(mjx-container) { max-width:100%; font-size:100%!important; overflow-x:auto; overflow-y:hidden; }
.rich-content :deep(mjx-container[jax="SVG"]>svg) { max-width:none; }
.rich-content :deep(mjx-assistive-mml) { overflow:hidden; }
.math-block { margin:14px 0; }
.problem-topline { display:flex; align-items:center; gap:12px; margin:0 0 9px; font-size:13px; color:var(--vp-c-text-3); }
.difficulty.easy,.solved-label { color:var(--lab-blue); }
.difficulty.medium { color:#9b720c; }
.difficulty.hard { color:var(--lab-red); }
.solved-label { margin-left:auto; }
.pytorch-lab h3.content-label { font-size:15px; font-weight:600; margin:26px 0 14px; }
.parameter-list { margin:0; font-size:15px; }
.parameter-list>div { margin:15px 0; }
.parameter-list dt { display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; }
.parameter-list dt code { font-size:13px; background:var(--vp-code-bg); color:var(--vp-code-color); }
.parameter-list dt span { font:12px/1.75 var(--vp-font-family-mono); color:var(--vp-c-text-2); }
.parameter-list dd { margin:6px 0 0; line-height:1.8; }
.pytorch-lab p.return-description { font-size:15px; line-height:1.9; margin:18px 0; }
.example-case { margin:26px 0; }
.pytorch-lab .example-case h3,.pytorch-lab .failed-case h3 { font-size:15px; font-weight:600; margin:0 0 12px; }
.example-body { border-left:2px solid var(--vp-c-divider); padding:4px 0 4px 15px; }
.example-label { font-weight:600; font-size:13px; display:block; margin:12px 0 6px; }
.pytorch-lab .example-case pre,.pytorch-lab .failed-case pre,.pytorch-lab .case-detail pre { background:transparent; padding:0; border:0; margin:0 0 12px; white-space:pre; overflow:auto; font:14px/1.85 var(--vp-font-family-mono); color:var(--vp-c-text-1); }
.pytorch-lab p.example-explanation { font-size:15px; line-height:1.9; margin:14px 0 4px; }
.pytorch-lab .constraint-list,.pytorch-lab .analysis-list { font-size:15px; line-height:1.9; margin:0; padding-left:20px; }
.pytorch-lab .constraint-list li,.pytorch-lab .analysis-list li { margin-top:10px; }
.pytorch-lab .solution-code { font:14px/1.85 var(--vp-font-family-mono); background:var(--vp-code-bg); padding:14px; overflow:auto; border:1px solid var(--vp-c-divider); border-radius:4px; }
.submission-summary { display:flex; align-items:center; gap:14px; padding:12px 0 22px; }
.status-icon { display:flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:50%; color:var(--lab-red); background:var(--lab-red-soft); flex-shrink:0; }
.accepted .status-icon { color:var(--lab-blue); background:var(--lab-blue-soft); }
.submission-summary .submission-title { display:block; font-size:22px; line-height:1.5; font-weight:600; color:var(--vp-c-text-1); }
.submission-count { display:block; margin-top:4px; color:var(--vp-c-text-2); font-size:13px; line-height:1.6; }
.failed-case { padding:22px 0; }
.failure-heading { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.pytorch-lab .failure-heading h3 { margin:0; }
.failure-heading select { padding:6px 9px; border:1px solid var(--vp-c-border); border-radius:4px; font-size:13px; color:var(--vp-c-text-2); background:var(--vp-c-bg); }
.pytorch-lab .failure-reason { font-size:14px; line-height:1.8; margin:10px 0 16px; color:var(--lab-red); }
.history-columns,.history-row { display:grid; grid-template-columns:100px 55px minmax(120px,1fr); align-items:center; gap:12px; padding:12px 10px; width:100%; text-align:left; font-size:14px; }
.history-columns { font-size:13px; color:var(--vp-c-text-3); border-bottom:1px solid var(--vp-c-divider); }
.history-row { border-bottom:1px solid var(--vp-c-divider); border-left:2px solid transparent; }
.history-row.selected { background:var(--lab-blue-soft); }
.history-columns>span:last-child,.history-row time { text-align:right; font-size:12px; color:var(--vp-c-text-3); }
.status-badge { width:fit-content; padding:3px 8px; border-radius:4px; font-size:13px; font-weight:500; line-height:1.6; }
.status-badge.pass { background:var(--lab-blue-soft); }
.status-badge.fail { background:var(--lab-red-soft); }
.pytorch-lab .empty-history,.pytorch-lab .case-error { font-size:14px; line-height:1.85; color:var(--vp-c-text-2); }
.editor-top { display:flex; align-items:center; gap:9px; min-height:47px; padding:0 15px; border-bottom:1px solid var(--vp-c-divider); background:var(--vp-c-bg); font-size:14px; font-weight:500; }
.engine-state { display:flex; align-items:center; gap:5px; margin-left:auto; font:11px var(--vp-font-family-mono); color:var(--vp-c-text-3); }
.engine-state i { width:5px; height:5px; border-radius:50%; background:var(--vp-c-text-3); }
.engine-state.online i { background:var(--lab-blue); }
.small-action { font-size:12px; color:var(--vp-c-text-2); padding:3px; }
.main-editor { flex:1; min-height:240px; overflow:hidden; }
.editor-actions { display:flex; justify-content:flex-end; gap:9px; padding:10px 14px; border-top:1px solid var(--vp-c-divider); border-bottom:1px solid var(--vp-c-divider); background:var(--vp-c-bg); }
.run-button,.submit-button { padding:7px 16px; border-radius:4px; font-size:14px; font-weight:500; }
.run-button { border:1px solid var(--vp-c-border); background:var(--vp-c-bg); }
.submit-button { background:#087fbd; color:#fff; }
.run-button:disabled,.submit-button:disabled { opacity:.5; cursor:wait; }
.results-pane { height:210px; flex:0 0 210px; overflow:auto; padding:15px 17px; }
.result-header { display:flex; align-items:center; gap:12px; font-size:14px; }
.result-header strong { font-weight:600; }
.result-time { margin-left:auto; font:12px var(--vp-font-family-mono); color:var(--vp-c-text-3); }
.pass { color:var(--lab-blue); }.fail { color:var(--lab-red); }
.pytorch-lab .stdout { background:transparent; border:0; padding:0; margin:14px 0 0; font:14px/1.85 var(--vp-font-family-mono); white-space:pre-wrap; overflow-wrap:anywhere; color:var(--vp-c-text-1); }
.pytorch-lab .result-placeholder,.pytorch-lab .connection-error { font-size:14px; color:var(--vp-c-text-3); margin:18px 0 0; line-height:1.8; }
.connection-error button { color:var(--lab-blue); }
.pytorch-lab .result-message { color:var(--lab-red); font-size:14px; line-height:1.8; margin:14px 0 0; }
.test-results { display:flex; gap:8px; flex-wrap:wrap; margin-top:16px; }
.test-case-button { padding:5px 9px; border:1px solid var(--vp-c-divider); border-radius:4px; font-size:13px; font-weight:500; }
.test-case-button.active { background:var(--vp-c-bg-soft); }
.case-detail { margin-top:14px; font-size:14px; }
.pytorch-lab .case-detail p { font-size:14px; line-height:1.8; }
.problem-section { padding:22px 0; }
.statement-section { padding-top:0; }
.problem-section:last-child { border-bottom:0; }
.pytorch-lab .section-heading { margin:0 0 16px; font-size:16px; line-height:1.5; font-weight:600; }
.problem-section .function-signature { margin:0 0 17px; }
.parameter-list>div { display:grid; grid-template-columns:minmax(90px,auto) 1fr; column-gap:15px; padding:10px 0; margin:0; }
.parameter-list dt { align-content:start; align-items:baseline; }
.parameter-list dd { margin:0; font-size:14px; line-height:1.8; }
.parameter-list dt span { font-size:12px; }
.pytorch-lab p.return-description { display:flex; align-items:baseline; gap:16px; margin:14px 0 0; padding-top:14px; border-top:1px dashed var(--vp-c-divider); font-size:14px; }
.return-description strong { flex-shrink:0; }
.example-case { margin:0 0 20px; }
.example-case:last-child { margin-bottom:0; }
.pytorch-lab .example-case h4 { font-size:14px; font-weight:600; line-height:1.6; margin:0 0 11px; }
.example-body { padding:13px 16px; background:var(--vp-code-bg); border:0; border-radius:6px; }
.example-line { display:grid; grid-template-columns:40px minmax(0,1fr); column-gap:12px; margin:0 0 9px; }
.example-line:last-child { margin-bottom:0; }
.example-line .example-label { margin:0; font-size:14px; font-weight:500; line-height:1.85; }
.pytorch-lab .example-case pre { margin:0; font-size:14px; background:transparent; }
.pytorch-lab .explanation p { margin:0; font-size:14px; line-height:1.85; color:var(--vp-c-text-2); }
.solution-block { position:relative; }
.submitted-code { margin:18px 0; }
.submitted-code summary { cursor:pointer; font-size:14px; font-weight:500; color:var(--vp-c-text-2); }
.pytorch-lab .solution-block .solution-code { padding-top:47px; margin:0; }
.copy-solution { position:absolute; display:flex; align-items:center; gap:5px; right:11px; top:10px; padding:4px 7px; font-size:12px; font-weight:500; color:var(--vp-c-text-2); border-radius:4px; }
.copy-solution:hover { color:var(--lab-blue); background:var(--lab-blue-soft); }
.panel-divider { display:flex; align-items:center; justify-content:center; flex:0 0 8px; cursor:row-resize; touch-action:none; background:transparent; outline:none; }
.panel-divider i { display:block; width:30px; height:2px; background:var(--vp-c-border); border-radius:2px; }
.panel-divider:focus-visible { outline:2px solid var(--lab-blue); outline-offset:-2px; border-radius:4px; }
.panel-divider:hover i,.panel-divider:focus-visible i,.resizing .panel-divider i { background:var(--lab-blue); }
.resizing { user-select:none; }
.main-editor { min-height:140px; }
@media(max-width:600px) { .parameter-list>div { grid-template-columns:1fr; row-gap:5px; }.example-body { padding:12px; }.example-line { grid-template-columns:36px minmax(0,1fr); gap:7px; } }

.pytorch-lab { font-variant-numeric:tabular-nums lining-nums; }
.history-row>span:not(.status-badge),.history-row time,.submission-count,.group-button small,.problem-navigation>span { font-family:var(--vp-font-family-mono); font-variant-numeric:tabular-nums lining-nums; font-feature-settings:"tnum" 1,"lnum" 1; }
.history-row time { white-space:nowrap; }
.pytorch-lab .submission-summary{position:relative;display:flex;align-items:center;margin:0 0 24px;padding:20px;border:1px solid #f2c7ce;border-radius:9px;background:var(--lab-red-soft)}.submission-summary.accepted{border-color:#c6e2f7;background:var(--lab-blue-soft)}.submission-summary.accepted .submission-title{color:var(--lab-blue)}.submission-summary .status-icon{width:30px;height:30px;flex-shrink:0}.pytorch-lab .submission-count{margin-top:8px;line-height:1.9}
.history-table{display:grid;gap:12px}.history-card{border:1px solid var(--vp-c-divider);border-radius:9px;background:var(--vp-c-bg);overflow:hidden}.history-card.selected{border-color:#c6e2f7}.history-row{display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:15px 16px;border:0;font-size:13px;min-height:58px}.history-row time{margin-right:auto;font-size:12px;text-align:left}.history-row .history-language{font-family:var(--vp-font-family-base);font-size:13px}.history-row .status-badge{font-family:var(--vp-font-family-base);white-space:nowrap}.history-chevron{font-size:16px;color:var(--vp-c-text-3)}.history-details{padding:0 16px 16px}.history-metrics{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 14px;font-size:12px;color:var(--vp-c-text-2);font-variant-numeric:tabular-nums}.history-details .solution-code{margin:0;border-radius:7px;background:var(--vp-c-bg);white-space:pre;overflow:auto}
.pytorch-lab .submission-summary:not(.accepted){background:var(--vp-c-bg);border-color:var(--vp-c-divider)}
.parameter-list>div { display:block; margin:0 0 18px; padding:0; }
.parameter-list dt { gap:10px; }
.parameter-list dd { margin-top:8px; font-size:15px; line-height:1.85; }
.parameter-list .parameter-type { background:transparent; padding:0; font-size:13px; color:var(--vp-c-text-2); }
.example-body { background:transparent; border-left:2px solid var(--vp-c-divider); border-radius:0; padding:0 0 0 16px; }
.example-line { display:block; margin:0; font-size:15px; line-height:1.85; }
.example-line .example-label { display:inline; margin-right:7px; font-size:15px; font-weight:600; }
.pytorch-lab .example-case pre { display:inline; white-space:pre-wrap; overflow-wrap:anywhere; font-size:14px; line-height:1.85; color:var(--vp-c-text-2); }
.pytorch-lab .example-line.explanation p { display:inline; font-size:15px; line-height:1.85; }
.pytorch-lab .example-case h4 { font-size:15px; margin-bottom:14px; }
.examples-section .example-case { margin-bottom:25px; }
.run-button,.submit-button { padding:4px 10px; height:30px; font-size:13px; line-height:20px; }

.example-line { display:grid; grid-template-columns:52px minmax(0,1fr); column-gap:0; }
.example-line .example-label { display:block; margin-right:0; }
.pytorch-lab .example-case pre,.pytorch-lab .example-line.explanation p { display:block; }

.lesson-steps,.variant-switch{display:flex;align-items:center;flex-wrap:wrap;gap:3px;width:fit-content;max-width:100%;padding:4px;margin-bottom:24px;border-radius:8px;background:var(--vp-code-bg)}
.lesson-steps button,.variant-switch button{display:flex;align-items:center;padding:6px 12px;font-size:13px;font-weight:500;color:var(--vp-c-text-2);border-radius:5px}
.lesson-steps button.active,.variant-switch button.active{color:var(--vp-c-text-1);background:var(--vp-c-bg);box-shadow:0 1px 3px #00000010}
.pytorch-lab h2.pane-title{overflow-wrap:anywhere;min-width:0}

.pytorch-lab button:focus-visible { outline:2px solid var(--lab-blue); outline-offset:2px; }
@media(max-width:950px) { .lab-grid { height:auto; min-height:0; }.work-area { grid-template-columns:minmax(0,1fr)!important; gap:8px; }.column-divider { display:none; }.learning-pane { height:520px; }.coding-pane { height:630px; }.work-area.single-pane .learning-pane,.work-area.single-pane .coding-pane { height:calc(100dvh - 120px); min-height:500px; } }
@media(max-width:950px) { .work-area.left-collapsed { grid-template-columns:28px minmax(0,1fr)!important; }.work-area.right-collapsed { grid-template-columns:minmax(0,1fr) 28px!important; } }
@media(max-width:600px) { .lab-grid { display:flex; flex-direction:column; }.learning-pane { height:500px; }.coding-pane { height:620px; }.learning-scroll { padding:20px 16px; }.small-action { font-size:12px; }.pytorch-lab h2.pane-title { font-size:22px; }.history-columns,.history-row { grid-template-columns:86px 40px minmax(105px,1fr); gap:5px; padding:10px 6px; }.history-row time { font-size:11px; } }
</style>
<style>
.pytorch-page .VPDoc { padding:20px 24px 24px!important; }
.pytorch-page .VPDoc .container { max-width:1600px!important; width:100%; }
.pytorch-page .VPDoc .content,.pytorch-page .VPDoc .content-container { max-width:none!important; width:100%!important; padding:0!important; }
.pytorch-page .VPDoc .aside,.pytorch-page .VPDocFooter { display:none; }
@media(max-width:600px) { .pytorch-page .VPDoc { padding:14px 10px!important; } }
</style>
