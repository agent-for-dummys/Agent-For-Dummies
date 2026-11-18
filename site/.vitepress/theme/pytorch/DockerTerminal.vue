<script setup lang="ts">
import {computed, onMounted, onUnmounted, ref, watch} from 'vue';
import {useData, withBase} from 'vitepress';
import type {Terminal} from '@xterm/xterm';
import type {FitAddon} from '@xterm/addon-fit';
import PaneExpandButton from './PaneExpandButton.vue';
import '@xterm/xterm/css/xterm.css';

const props = defineProps<{level?: number; dockerfile?: string; makefile?: string; taskId?: string; files?: Record<string,string>; expanded: boolean}>();
const emit = defineEmits<{expand: []; file:[name:string,content:string]}>();
const label = computed(() => props.taskId?.startsWith('linux') ? 'Linux' : props.taskId?.startsWith('git') ? 'Git' : 'Docker');
const syncedFiles = computed(() => props.files ?? {dockerfile:props.dockerfile ?? '',Makefile:props.makefile ?? ''});
const {isDark} = useData();
const host = ref<HTMLElement>();
let terminal: Terminal | undefined;
let fit: FitAddon | undefined;
let socket: WebSocket | undefined;
let intersection: IntersectionObserver | undefined;
let resize: ResizeObserver | undefined;
const lastDraft: Record<string,string> = {};
let unmounted = false;

function theme() {
  return isDark.value
    ? {background: '#252b34', foreground: '#e4e9f0', cursor: '#78c6f2', selectionBackground: '#334d67', blue: '#78c6f2'}
    : {background: '#f7f9fc', foreground: '#252b36', cursor: '#0087be', selectionBackground: '#dcedfb', blue: '#0073a2'};
}

function send(event: object) {
  if (socket?.readyState !== WebSocket.OPEN) return false;
  socket.send(JSON.stringify(event));
  return true;
}

function saveDraft() {
  const files = syncedFiles.value;
  for (const file of Object.keys(files)) {
    if (lastDraft[file] !== files[file] && send({type: 'draft', file, draft: files[file]})) lastDraft[file] = files[file];
  }
}

async function connect(element: HTMLElement) {
  const [{Terminal}, {FitAddon}] = await Promise.all([import('@xterm/xterm'), import('@xterm/addon-fit')]);
  if (unmounted) return;
  terminal = new Terminal({fontFamily: getComputedStyle(element).getPropertyValue('--vp-font-family-mono'),
    fontSize: 13, lineHeight: 1.35, cursorBlink: true, scrollback: 3000, theme: theme()});
  fit = new FitAddon();
  terminal.loadAddon(fit);
  terminal.open(element);
  terminal.textarea?.setAttribute('aria-label', label.value + ' 终端输入');
  resize = new ResizeObserver(() => {
    if (element.clientWidth && element.clientHeight) fit?.fit();
  });
  resize.observe(element);
  fit.fit();

  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) {
    terminal.writeln('请在已克隆的项目目录运行 npm run learn，再从本地练习页打开终端。');
    return;
  }

  const url = new URL(withBase('/__local-docker-practice'), location.href);
  url.protocol = 'ws:';
  if (props.taskId) url.searchParams.set('task', props.taskId);
  else url.searchParams.set('level', String(props.level));
  socket = new WebSocket(url);
  socket.addEventListener('open', () => {
    if (!terminal) return;
    Object.assign(lastDraft, syncedFiles.value);
    send({type: 'start', files: lastDraft, cols: terminal.cols, rows: terminal.rows});
  });
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.type === 'file') {lastDraft[message.file] = message.data; emit('file',message.file,message.data);}
    if (message.type === 'output') terminal?.write(message.data);
    if (message.type === 'message') terminal?.writeln('\r\n' + message.data);
  });
  socket.addEventListener('error', () => terminal?.writeln('\r\n连接本地服务失败。请用 npm run learn 启动后刷新页面。'));
  socket.addEventListener('close', event => {
    if (event.wasClean) terminal?.writeln('\r\n终端连接已关闭。刷新页面可以重新打开。');
  });
  terminal.onResize(({cols, rows}) => send({type: 'resize', cols, rows}));
  terminal.onData(data => {
    saveDraft();
    send({type: 'input', data});
  });
}

watch(syncedFiles, saveDraft, {deep:true});
defineExpose({read: (file:string) => send({type:'read',file})});
watch(isDark, () => { if (terminal) terminal.options.theme = theme(); });

onMounted(() => {
  const element = host.value;
  if (!element) return;
  intersection = new IntersectionObserver(entries => {
    if (!entries.some(entry => entry.isIntersecting)) return;
    intersection?.disconnect();
    void connect(element).catch(() => {
      element.textContent = '终端加载失败，请刷新页面重试。';
    });
  });
  intersection.observe(element);
});
onUnmounted(() => {
  unmounted = true;
  intersection?.disconnect();
  resize?.disconnect();
  socket?.close();
  terminal?.dispose();
});
</script>

<template>
  <section class="terminal-panel" :class="{expanded}" :aria-label="label + ' 终端'">
    <header class="terminal-toolbar">
      <span class="terminal-tab">终端</span>
      <PaneExpandButton :expanded="expanded" label="终端" @toggle="emit('expand')"/>
    </header>
    <div ref="host" class="terminal-surface"/>
  </section>
</template>

<style scoped>
.terminal-panel{display:flex;flex-direction:column;flex:none;min-height:48px;max-height:calc(100% - 160px);border:1px solid var(--vp-c-divider);border-radius:10px;background:var(--vp-c-bg);overflow:hidden}
.terminal-panel.expanded{height:100%!important;flex:1;max-height:none}
.terminal-toolbar{display:flex;align-items:center;gap:7px;min-height:46px;padding:6px 10px;border-bottom:1px solid var(--vp-c-divider);flex:none}
.terminal-tab{padding:5px 8px;border-radius:5px;font-size:13px;font-weight:500;color:var(--lab-blue);background:var(--lab-blue-soft);margin-right:auto}
.terminal-surface{flex:1;overflow:hidden;min-height:0;padding:8px 10px;background:var(--vp-code-bg)}
</style>
