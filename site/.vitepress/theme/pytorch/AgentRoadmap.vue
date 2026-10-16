<script setup lang="ts">
import {computed,onMounted,onUnmounted,ref} from 'vue';
const props=defineProps<{course:any;completed:string[];bookmarkTop:number}>();
const emit=defineEmits<{select:[id:string];close:[]}>();
type Point={x:number;y:number};
const canvas=ref<HTMLElement>(),zoom=ref(1),pan=ref<Point>({x:0,y:0});
const navBottom=ref(64),dragging=ref(false),draggedNode=ref('');
const cardWidth=236,cardHeight=104,storageKey='agent-roadmap-layout-v6';
const layout=[
 {id:'basics',group:'认识 Agent',x:0,y:220},
 {id:'tools',group:'工具与 Agent',x:340,y:220},
 {id:'graph',group:'用图控制流程',x:340,y:0},
 {id:'retrieval',group:'检索与扩展',x:680,y:440},
 {id:'runtime',group:'拆解 Pi 的运行循环',x:680,y:220},
 {id:'sessions',group:'让 Pi 持续工作',x:1020,y:0},
 {id:'project',group:'扩展与组装',x:1360,y:220},
];
const initialPositions=()=>Object.fromEntries(layout.map(n=>[n.id,{x:n.x,y:n.y}]));
const positions=ref<Record<string,Point>>(initialPositions());
const nodes=computed(()=>layout.map(node=>{
 const chapters=props.course.chapters.filter((ch:any)=>ch.group===node.group);
 const count=chapters.filter((ch:any)=>props.completed.includes(ch.id)).length;
 return {...node,chapters,count,progress:chapters.length?count/chapters.length:0};
}));
// These links show prerequisites used by a section, rather than catalog order.
// RAG starts from model calls, while its MCP lessons also build on tools.
// Persistent Pi execution combines the hand-written loop with graph checkpoints.
const edges=[['basics','tools'],['basics','graph'],['basics','retrieval'],['tools','retrieval'],['tools','runtime'],['graph','sessions'],['runtime','sessions'],['retrieval','project'],['sessions','project']];
const paths=computed(()=>edges.map(([from,to])=>{
 const a=positions.value[from],b=positions.value[to],dx=b.x-a.x,dy=b.y-a.y;
 // Keep the long foundation-to-retrieval branch below the tool cards.
 if(from==='basics'&&to==='retrieval'&&dx>cardWidth&&dy>cardHeight){
  const ax=a.x+cardWidth/2,ay=a.y+cardHeight+6,bx=b.x-9,by=b.y+cardHeight/2;
  return `M ${ax} ${ay} C ${ax} ${by}, ${bx-120} ${by}, ${bx} ${by}`;
 }
 // Select attachment sides from the current positions, including reversed cards.
 if(Math.abs(dx)>Math.abs(dy)*.85){
  const sign=dx>=0?1:-1,ax=a.x+(sign>0?cardWidth:0),bx=b.x+(sign>0?0:cardWidth);
  const ay=a.y+cardHeight/2,by=b.y+cardHeight/2,bend=Math.max(48,Math.abs(bx-ax)*.5);
  return `M ${ax+sign*6} ${ay} C ${ax+sign*bend} ${ay}, ${bx-sign*bend} ${by}, ${bx-sign*9} ${by}`;
 }
 const sign=dy>=0?1:-1,ax=a.x+cardWidth/2,bx=b.x+cardWidth/2;
 const ay=a.y+(sign>0?cardHeight:0),by=b.y+(sign>0?0:cardHeight),bend=Math.max(48,Math.abs(by-ay)*.5);
 return `M ${ax} ${ay+sign*6} C ${ax} ${ay+sign*bend}, ${bx} ${by-sign*bend}, ${bx} ${by-sign*9}`;
}));
let origin:{pointer:number;client:Point;start:Point;node:string}|undefined;
let moved=false,suppressClick=false,lastFocus:HTMLElement|null=null,observer:ResizeObserver|undefined;
function saveLayout(){try{localStorage.setItem(storageKey,JSON.stringify(positions.value));}catch{}}
function restoreLayout(){
 try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');
  for(const node of layout){const p=saved?.[node.id];if(p&&Number.isFinite(p.x)&&Number.isFinite(p.y)&&Math.abs(p.x)<10000&&Math.abs(p.y)<10000)positions.value[node.id]={x:p.x,y:p.y};}
 }catch{}
}
function measureNav(){navBottom.value=Math.max(0,document.querySelector<HTMLElement>('.VPNav')?.getBoundingClientRect().bottom||0);}
function fit(){
 if(!canvas.value)return;
 const {width,height}=canvas.value.getBoundingClientRect(),points=Object.values(positions.value);
 const minX=Math.min(...points.map(p=>p.x)),minY=Math.min(...points.map(p=>p.y));
 const worldWidth=Math.max(...points.map(p=>p.x))+cardWidth-minX;
 const worldHeight=Math.max(...points.map(p=>p.y))+cardHeight-minY;
 zoom.value=Math.min(1.15,Math.max(width<700?.85:.62,Math.min((width-120)/worldWidth,(height-140)/worldHeight)));
 pan.value={x:(width<700?70:(width-worldWidth*zoom.value)/2)-minX*zoom.value,y:(height-worldHeight*zoom.value)/2-minY*zoom.value};
}
function reset(){positions.value=initialPositions();saveLayout();fit();}
function wheel(event:WheelEvent){
 event.preventDefault();const rect=canvas.value!.getBoundingClientRect(),px=event.clientX-rect.left,py=event.clientY-rect.top;
 const before=zoom.value,after=Math.min(2,Math.max(.35,before*Math.exp(-event.deltaY*.0015)));
 pan.value={x:px-(px-pan.value.x)*after/before,y:py-(py-pan.value.y)*after/before};zoom.value=after;
}
function down(event:PointerEvent){
 if(event.button!==0||(event.target as HTMLElement).closest('.map-controls,.map-bookmark'))return;
 const target=(event.target as HTMLElement).closest<HTMLElement>('[data-section]'),node=target?.dataset.section||'';
 origin={pointer:event.pointerId,client:{x:event.clientX,y:event.clientY},start:{...(node?positions.value[node]:pan.value)},node};
 moved=false;suppressClick=false;target?.focus({preventScroll:true});canvas.value?.setPointerCapture(event.pointerId);
}
function move(event:PointerEvent){
 if(!origin||origin.pointer!==event.pointerId)return;
 const dx=event.clientX-origin.client.x,dy=event.clientY-origin.client.y;
 if(Math.hypot(dx,dy)>5)moved=true;if(!moved)return;
 dragging.value=true;draggedNode.value=origin.node;
 if(origin.node)positions.value[origin.node]={x:origin.start.x+dx/zoom.value,y:origin.start.y+dy/zoom.value};
 else pan.value={x:origin.start.x+dx,y:origin.start.y+dy};
}
function end(event:PointerEvent,cancel=false){
 if(!origin||origin.pointer!==event.pointerId)return;
 const node=origin.node;origin=undefined;dragging.value=false;draggedNode.value='';suppressClick=moved;
 if(canvas.value?.hasPointerCapture(event.pointerId))canvas.value.releasePointerCapture(event.pointerId);
 if(moved&&node)saveLayout();if(!moved&&!cancel&&node)select(node);
}
function select(id:string){
 const node=nodes.value.find(n=>n.id===id);
 const chapter=node?.chapters.find((ch:any)=>!props.completed.includes(ch.id))||node?.chapters[0];
 if(chapter)emit('select',chapter.id);
}
function click(event:MouseEvent,id:string){if(event.detail===0&&!suppressClick)select(id);suppressClick=false;}
function nodeKey(event:KeyboardEvent,id:string){
 if(event.key==='Enter'||event.key===' ')suppressClick=false;
 const deltas:Record<string,Point>={ArrowLeft:{x:-20,y:0},ArrowRight:{x:20,y:0},ArrowUp:{x:0,y:-20},ArrowDown:{x:0,y:20}};
 const d=deltas[event.key];if(!d)return;event.preventDefault();
 positions.value[id]={x:positions.value[id].x+d.x,y:positions.value[id].y+d.y};saveLayout();
}
function key(event:KeyboardEvent){if(event.key==='Escape'&&!document.querySelector('dialog[open],.VPLocalSearchBox'))emit('close');}
function resize(){measureNav();fit();}
onMounted(()=>{
 lastFocus=document.activeElement as HTMLElement;measureNav();restoreLayout();requestAnimationFrame(fit);
 canvas.value?.querySelector<HTMLElement>('.map-bookmark')?.focus({preventScroll:true});
 const nav=document.querySelector('.VPNav');observer=new ResizeObserver(measureNav);if(nav)observer.observe(nav);
 window.addEventListener('resize',resize);window.addEventListener('scroll',measureNav,{passive:true});window.addEventListener('keydown',key);
});
onUnmounted(()=>{observer?.disconnect();window.removeEventListener('resize',resize);window.removeEventListener('scroll',measureNav);window.removeEventListener('keydown',key);if(document.activeElement===document.body)lastFocus?.focus({preventScroll:true});});
</script>
<template>
 <Teleport to="body">
  <div ref="canvas" class="mini-pi-map" :class="{dragging}" :style="{top:navBottom+'px'}" role="region" aria-label="Agent 学习路线图" @wheel="wheel" @pointerdown="down" @pointermove="move" @pointerup="end($event)" @pointercancel="end($event,true)">
   <button class="map-bookmark" :style="{top:Math.max(20,bookmarkTop-navBottom)+'px'}" type="button" aria-label="收回路线图" title="收回路线图" @click="emit('close')"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2V5Zm6-2v16m6-14v16"/></svg></button>
   <div class="map-controls"><button type="button" aria-label="复位路线图" title="复位路线图" @click="reset"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M8 12h8m-4-4v8"/></svg></button></div>
   <div class="map-world" :style="{transform:`translate(${pan.x}px,${pan.y}px) scale(${zoom})`}">
    <svg class="map-edges" aria-hidden="true"><defs><marker id="mini-pi-arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M1 1 L5 3.5 L1 6"/></marker></defs><path v-for="(path,i) in paths" :key="i" :d="path" class="map-link" marker-end="url(#mini-pi-arrow)"/></svg>
    <button v-for="node in nodes" :key="node.id" type="button" class="map-node" :class="{done:node.progress===1,'node-dragging':draggedNode===node.id}" :data-section="node.id" :style="{left:positions[node.id].x+'px',top:positions[node.id].y+'px'}" :aria-label="`${node.group}，已完成 ${node.count}/${node.chapters.length}，方向键移动，回车进入`" @click="click($event,node.id)" @keydown="nodeKey($event,node.id)">
     <span class="node-title">{{node.group}}</span>
     <span class="node-progress" role="progressbar" :aria-label="node.group+'学习进度'" :aria-valuenow="node.count" :aria-valuemin="0" :aria-valuemax="node.chapters.length"><i :style="{width:node.progress*100+'%'}"/></span>
    </button>
   </div>
  </div>
 </Teleport>
</template>
<style scoped>
.mini-pi-map{position:fixed;inset:64px 0 0;z-index:29;overflow:hidden;touch-action:none;overscroll-behavior:contain;cursor:grab;background:var(--vp-c-bg);color:var(--vp-c-text-1);font-family:var(--vp-font-family-base);isolation:isolate}
.mini-pi-map:before{content:'';position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at 50% 48%,#eaf2fc45,transparent 68%)}
.mini-pi-map.dragging{cursor:grabbing;user-select:none}
.map-world{position:absolute;left:0;top:0;width:1596px;height:544px;transform-origin:0 0;will-change:transform}
.map-edges{position:absolute;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none;color:#b9c4d1}
.map-link{fill:none;stroke:currentColor;stroke-width:1.6}
.map-edges marker path{fill:none;stroke:currentColor;stroke-width:1.2;stroke-linecap:round;stroke-linejoin:round}
.map-node{position:absolute;width:236px;height:104px;display:flex;flex-direction:column;justify-content:center;gap:21px;padding:23px 27px;border:1px solid #dce3ec;border-radius:16px;background:#fff;color:#354355;box-shadow:0 3px 5px #29466b03,0 12px 32px -14px #29466b22;cursor:grab;user-select:none;transition:box-shadow .18s,border-color .18s,background .18s}
.node-title{font-size:17px;line-height:24px;font-weight:550;letter-spacing:.1px;white-space:nowrap;text-align:left}
.node-progress{display:block;flex-shrink:0;height:4px;width:100%;border-radius:4px;background:#e9edf2;overflow:hidden}
.node-progress i{display:block;height:100%;background:#299bcc;border-radius:4px;transition:width .2s}
.map-node.done{border-color:#bcdbe9}
.map-node:hover{border-color:#9fc8de;box-shadow:0 5px 9px #29466b06,0 18px 36px -14px #29466b35}
.map-node:focus-visible{outline:2px solid #399bd0;outline-offset:5px}
.map-node.node-dragging{cursor:grabbing;border-color:#6eb4d8;box-shadow:0 10px 34px #29466b26;z-index:1}
.map-bookmark{position:absolute;z-index:2;left:0;display:grid;place-items:center;width:30px;height:36px;transform:translateY(-50%);padding:0;background:var(--vp-c-default-soft);border:1px solid var(--vp-c-divider);border-left:none;border-radius:0 6px 6px 0;color:#1685bb;cursor:pointer}
.map-bookmark svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.map-controls{position:absolute;z-index:2;right:24px;bottom:24px}
.map-controls button{display:grid;place-items:center;width:38px;height:38px;border:1px solid var(--vp-c-divider);border-radius:10px;background:var(--vp-c-bg);color:var(--vp-c-text-2);cursor:pointer}
.map-controls button:hover{color:#1685bb;border-color:#9fc8de}
.map-controls svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}
.dark .mini-pi-map:before{background:radial-gradient(ellipse at 50% 48%,#263c532b,transparent 68%)}
.dark .map-node{background:#252b34;border-color:#414c5b;color:#dbe3ee;box-shadow:0 12px 32px -14px #0005}
.dark .map-node:hover,.dark .map-node.node-dragging{border-color:#5a9fbe}
.dark .map-node.done{border-color:#427d97}
.dark .node-progress{background:#414b58}
.dark .map-edges{color:#637185}
@media(prefers-reduced-motion:reduce){.map-node,.node-progress i{transition:none}}
</style>
