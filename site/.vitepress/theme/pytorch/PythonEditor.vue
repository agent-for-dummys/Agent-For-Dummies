<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';
import { useData } from 'vitepress';
import { loadEditorRuntime, prepareLearningPage } from './editor-runtime';
const props=withDefaults(defineProps<{modelValue:string;contextKey?:string;readonly?:boolean;language?:'python'|'text';lineWrapping?:boolean;focusMarker?:string}>(),{readonly:false,contextKey:'default',language:'python',lineWrapping:false,focusMarker:''});
const emit=defineEmits<{ 'update:modelValue':[value:string];run:[];ready:[] }>();
const host=ref<HTMLElement>(),ready=ref(false);const {isDark}=useData();
let editor:any, compartment:any, makeTheme:any, createState:any, currentKey=props.contextKey;
const states=new Map<string,any>();
let syncing=false;
let focusTask=()=>{};
onMounted(async()=>{
 await prepareLearningPage();
 const [{EditorView,basicSetup},{python},{keymap},{indentWithTab},{Compartment,EditorState},{indentUnit,HighlightStyle,syntaxHighlighting},{tags}]=await loadEditorRuntime();
 if(!host.value)return;
 compartment=new Compartment();makeTheme=()=>[EditorView.theme({'&':{height:'100%',color:'var(--vp-c-text-1)',backgroundColor:'var(--vp-c-bg)'},'.cm-scroller':{fontFamily:'var(--vp-font-family-mono)',fontSize:'14px',lineHeight:'1.8'},'.cm-gutters':{backgroundColor:'var(--vp-c-bg-alt)',color:'var(--vp-c-text-3)',borderRight:'1px solid var(--vp-c-divider)'},'.cm-activeLine,.cm-activeLineGutter':{backgroundColor:'var(--vp-c-bg-soft)'},'&.has-selection .cm-activeLine, &.has-selection .cm-activeLineGutter':{backgroundColor:'transparent'},'.cm-selectionMatch':{backgroundColor:'transparent'},'.cm-cursor':{borderLeftColor:'var(--lab-blue)'},'&.cm-focused':{outline:'none'},'.cm-selectionBackground, &.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground':{backgroundColor:'var(--lab-selection)'},'.cm-content::selection, .cm-content ::selection':{color:'var(--lab-token-color, var(--vp-c-text-1))'},'.cm-content':{padding:'12px 0'},'.cm-line':{padding:'0 12px'}},{dark:isDark.value}),syntaxHighlighting(HighlightStyle.define([
  {tag:tags.keyword,color:isDark.value?'#caa6ef':'#8950a4'},
  {tag:tags.string,color:isDark.value?'#b7ce99':'#417347'},
  {tag:[tags.number,tags.bool],color:isDark.value?'#8ccbae':'#246985'},
  {tag:tags.comment,color:isDark.value?'#93a4b4':'#667b8b'},
  {tag:[tags.function(tags.variableName),tags.typeName],color:isDark.value?'#87b7d7':'#167cb5'}
 ].map(style=>({...style,'--lab-token-color':style.color}))))];
 createState=(doc:string)=>EditorState.create({doc,extensions:[basicSetup,...(props.lineWrapping?[EditorView.lineWrapping]:[]),...(props.language==='python'?[python()]:[]),indentUnit.of('    '),EditorState.readOnly.of(props.readonly),EditorView.editorAttributes.of(view=>({class:view.state.selection.ranges.some(range=>!range.empty)?'has-selection':''})),EditorView.contentAttributes.of({'aria-label':props.language==='python'?'Python 代码编辑器':'文件编辑器',spellcheck:'false',autocorrect:'off',autocapitalize:'off'}),keymap.of([indentWithTab,{key:'Mod-Enter',run:()=>{emit('run');return true;}}]),compartment.of(makeTheme()),EditorView.updateListener.of(update=>{if(update.docChanged&&!syncing)emit('update:modelValue',update.state.doc.toString());})]});
 currentKey=props.contextKey;editor=new EditorView({state:createState(props.modelValue),parent:host.value});ready.value=true;emit('ready');
 focusTask=()=>{if(!props.focusMarker||!editor)return;const position=editor.state.doc.toString().indexOf(props.focusMarker);if(position>=0)editor.dispatch({selection:{anchor:position},effects:EditorView.scrollIntoView(position,{y:'center'})});};
 focusTask();
});
watch([()=>props.contextKey,()=>props.modelValue],([contextKey,value])=>{
 if(!editor)return;
 syncing=true;
 try{
  if(contextKey!==currentKey){
   states.set(currentKey,editor.state);currentKey=contextKey;
   const saved=states.get(contextKey);
   editor.setState(saved?.doc.toString()===value?saved:createState(value));
   editor.dispatch({effects:compartment.reconfigure(makeTheme())});
   if(!saved)focusTask();
  }else if(editor.state.doc.toString()!==value){
   // Resets are intentional external replacements. Do not echo them back into
   // v-model, especially while an input method is committing a composition.
   editor.setState(createState(value));
  }
 }finally{syncing=false;}
},{flush:'post'});
watch(isDark,()=>{if(editor)editor.dispatch({effects:compartment.reconfigure(makeTheme())});});
onUnmounted(()=>editor?.destroy());
</script>

<template><div class="python-editor"><div ref="host" class="editor-host"/><div v-if="!ready" class="editor-loading" role="status">正在加载编辑器…</div></div></template>
<style scoped>.python-editor,.editor-host { height:100%;min-height:0; }.python-editor { position:relative;overflow:hidden; }.editor-loading {position:absolute;inset:0;padding:20px;color:var(--vp-c-text-3);font-size:14px}.editor-host :deep(.cm-scroller){overflow:auto;font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0;}</style>
