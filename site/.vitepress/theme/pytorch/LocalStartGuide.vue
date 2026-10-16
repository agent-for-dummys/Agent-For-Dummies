<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
const props=defineProps<{open:boolean}>();
const emit=defineEmits<{close:[]}>();
const dialog=ref<HTMLDialogElement>();
watch(()=>props.open,async value=>{await nextTick();if(value&&!dialog.value?.open)dialog.value?.showModal();else if(!value&&dialog.value?.open)dialog.value.close();});
</script>
<template>
 <dialog ref="dialog" class="local-start-guide" aria-labelledby="local-guide-title" @cancel="emit('close')" @close="emit('close')" @click="($event.target===dialog)&&emit('close')">
  <header><h2 id="local-guide-title">友情提示</h2><button type="button" aria-label="关闭友情提示" @click="emit('close')">×</button></header>
  <p>需要拉取源码，在自己电脑上安装 Node.js 22 或更新版本，以及 Python 3.12～3.14。下载或克隆项目后，在项目目录中打开终端。</p>
  <a href="https://github.com/agent-for-dummys/Agent-For-Dummies" target="_blank" rel="noopener noreferrer"><strong>获取项目 ↗</strong></a>
  <h3>首次安装</h3><pre>npm run setup</pre><p>安装项目环境。</p>
  <h3>开始练习</h3><pre>npm run learn</pre><p>浏览器会自动打开练习页面。运行时记得不要关闭运行中的终端窗口，按 Ctrl+C 可以结束服务。</p>
  <a href="http://127.0.0.1:4173/practice" target="_blank" rel="noopener noreferrer"><strong>打开本地练习页面 ↗</strong></a>
 </dialog>
</template>
<style scoped>
.local-start-guide{width:min(520px,calc(100vw - 32px));max-height:calc(100dvh - 48px);overflow:auto;padding:24px;border:1px solid var(--vp-c-border);border-radius:10px;background:var(--vp-c-bg);color:var(--vp-c-text-1);margin:auto;box-shadow:0 12px 40px #00000018}.local-start-guide::backdrop{background:#17273755}.local-start-guide header{display:flex;justify-content:space-between;align-items:center;gap:12px}.local-start-guide h2{margin:0;padding:0;border:0;font-size:21px;font-weight:600}.local-start-guide header button{font-size:25px;line-height:28px;color:var(--vp-c-text-2);width:28px}.local-start-guide h3{font-size:15px;margin:22px 0 10px}.local-start-guide p{font-size:14px;line-height:1.8;margin:12px 0}.local-start-guide pre{font:14px/1.8 var(--vp-font-family-mono);background:var(--vp-code-bg);border-radius:5px;padding:10px 13px;margin:0;white-space:pre-wrap}.local-start-guide a{color:var(--lab-blue);font-size:14px}.local-start-guide button:focus-visible,.local-start-guide a:focus-visible{outline:2px solid var(--lab-blue);outline-offset:2px}
</style>
