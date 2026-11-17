<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue';
import main from '../../../../exercises/docker/main.cpp?raw';
import makefile from '../../../../exercises/docker/Makefile?raw';
import AgentCodeBlock from './AgentCodeBlock.vue';
import FileWorkspaceEditor from './FileWorkspaceEditor.vue';
import PythonEditor from './PythonEditor.vue';
import {cppDockerExample, dockerExample, dockerTasks, expectedOutput, multiStageDockerExample} from './docker-course';
import type {NavigationState} from './course-navigation';
import WorkspaceDivider from './WorkspaceDivider.vue';
import {useFileWorkspaceLayout} from './file-workspace-layout';
import DockerTerminal from './DockerTerminal.vue';
import './agent-code.css';

const emit = defineEmits<{navigation: [state: NavigationState]}>();
const storageKey = 'development-docker-v1';
const files = ['main.cpp', 'Makefile', 'dockerfile'];
const filename = ref('dockerfile');
const index = ref(0);
const completed = ref<string[]>([]);
const drafts = ref<Record<string, string>>({});
const makefileDrafts = ref<Record<string, string>>({});
const tab = ref<'task' | 'example'>('task');
const learningScroll = ref<HTMLElement>();
const {splitter, codePane, split, bottomHeight, runExpanded, startSplit, dragSplit, stepSplit, startHeight, dragHeight, stepHeight} = useFileWorkspaceLayout();
const task = computed(() => dockerTasks[index.value]);
const draft = computed(() => drafts.value[task.value.id] ?? '');
const content = computed({
  get: () => {
    if (filename.value === 'dockerfile') return draft.value;
    if (filename.value === 'Makefile') return makefileDrafts.value[task.value.id] ?? makefile;
    return main;
  },
  set: value => {
    if (filename.value === 'dockerfile') drafts.value[task.value.id] = value;
    if (filename.value === 'Makefile') makefileDrafts.value[task.value.id] = value;
  },
});
const done = computed(() => completed.value.includes(task.value.id));

function selectTarget(id: string) {
  const next = dockerTasks.findIndex(entry => entry.id === id);
  if (next < 0) return false;
  index.value = next;
  tab.value = 'task';
  learningScroll.value?.scrollTo({top: 0});
  return true;
}

function carryForward() {
  const firstTask = dockerTasks[0].id;
  drafts.value[task.value.id] = drafts.value[firstTask];
  if (makefileDrafts.value[task.value.id] === undefined && makefileDrafts.value[firstTask] !== undefined) {
    makefileDrafts.value[task.value.id] = makefileDrafts.value[firstTask];
  }
  filename.value = 'dockerfile';
}

function toggleComplete() {
  const id = task.value.id;
  completed.value = done.value ? completed.value.filter(value => value !== id) : [...completed.value, id];
}

onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
    for (const {id} of dockerTasks) {
      if (typeof saved?.drafts?.[id] === 'string') drafts.value[id] = saved.drafts[id];
      if (typeof saved?.makefileDrafts?.[id] === 'string') makefileDrafts.value[id] = saved.makefileDrafts[id];
    }
    if (Array.isArray(saved?.completed)) completed.value = dockerTasks.map(({id}) => id).filter(id => saved.completed.includes(id));
  } catch {}
  emit('navigation', {selected: task.value.id, completed: completed.value});
});

watch([drafts, makefileDrafts, completed], () => {
  try { localStorage.setItem(storageKey, JSON.stringify({drafts: drafts.value, makefileDrafts: makefileDrafts.value, completed: completed.value})); } catch {}
}, {deep: true});
watch([task, completed], () => emit('navigation', {selected: task.value.id, completed: completed.value}));
defineExpose({selectTarget});
</script>

<template>
  <div class="agent-ide">
    <div ref="splitter" class="agent-panels" :style="{'--lesson-share': split + 'fr', '--editor-share': (1 - split) + 'fr'}">
      <section class="learning-pane">
        <header class="learning-tabs">
          <button type="button" :class="{active: tab === 'task'}" :aria-pressed="tab === 'task'" @click="tab = 'task'">任务</button>
          <button type="button" :class="{active: tab === 'example'}" :aria-pressed="tab === 'example'" @click="tab = 'example'">dockerfile 示例</button>
          <nav class="task-arrows" aria-label="切换关卡">
            <button type="button" aria-label="上一关" :disabled="index === 0" @click="selectTarget(dockerTasks[index - 1].id)">‹</button>
            <span>{{ index + 1 }} / {{ dockerTasks.length }}</span>
            <button type="button" aria-label="下一关" :disabled="index === dockerTasks.length - 1" @click="selectTarget(dockerTasks[index + 1].id)">›</button>
          </nav>
        </header>
        <article ref="learningScroll" class="learning-content">
          <h1>{{ task.title }}</h1>
          <template v-if="tab === 'task'">
            <p>{{ task.goal }}</p>
            <h2>编写要求</h2>
            <ol><li v-for="requirement in task.requirements" :key="requirement">{{ requirement }}</li></ol>
            <h2>预期输出</h2>
            <pre><code>{{ expectedOutput }}</code></pre>
            <h2>验证指令：</h2>
            <AgentCodeBlock :code="task.commands"/>
            <details class="docker-hint">
              <summary>提示</summary>
              <p>{{ task.hint }}</p>
            </details>
            <button type="button" class="docker-action" :aria-pressed="done" @click="toggleComplete">{{ done ? '已完成 · 取消标记' : '标记本关已完成' }}</button>
          </template>
          <template v-else-if="index === 0">
            <h2>最小示例</h2>
            <p>这个示例从 Ubuntu 镜像启动一个容器，让它打印 <code>Hello, Docker!</code>。</p>
            <AgentCodeBlock :code="dockerExample"/>

            <h2>编译 C++ 程序</h2>
            <p>这个示例先安装编译工具，再把 <code>main.cpp</code> 复制进镜像，用 <code>RUN</code> 编译，并用 <code>CMD</code> 启动编译好的程序。</p>
            <AgentCodeBlock :code="cppDockerExample"/>
          </template>
          <template v-else>
            <h2>多阶段构建</h2>
            <p>第一阶段取名为 <code>builder</code>，在 Ubuntu 里安装工具并编译。第二阶段从空的 <code>scratch</code> 开始，用 <code>COPY --from=builder</code> 取出单个可执行文件。</p>
            <AgentCodeBlock :code="multiStageDockerExample"/>
            <p>在 <code>g++</code> 命令里加 <code>-static</code>，就不需要到 <code>scratch</code> 里查找动态库，因此需要把 <code>-static</code> 静态链接选项放到 Makefile 里，再用 <code>RUN make</code> 编译。</p>
          </template>
        </article>
      </section>
      <WorkspaceDivider axis="x" label="调整学习区与代码区宽度" @start="startSplit" @drag="dragSplit" @step="stepSplit"/>
      <section ref="codePane" class="coding-pane">
        <FileWorkspaceEditor v-show="!runExpanded" :files="files" :filename="filename" @select="filename = $event">
          <template #actions>
            <button v-if="index === 1 && filename === 'dockerfile' && !draft && drafts[dockerTasks[0].id]" type="button" class="docker-action" @click="carryForward">沿用第 1 关</button>
          </template>
          <PythonEditor v-model="content" :context-key="task.id + ':' + filename" :readonly="filename === 'main.cpp'" language="text" :line-wrapping="true"/>
        </FileWorkspaceEditor>
        <WorkspaceDivider v-show="!runExpanded" axis="y" label="调整运行区高度" @start="startHeight" @drag="dragHeight" @step="stepHeight"/>
        <DockerTerminal v-for="(entry, i) in dockerTasks" v-show="i === index" :key="entry.id"
          :level="i + 1" :dockerfile="drafts[entry.id] ?? ''" :makefile="makefileDrafts[entry.id] ?? makefile" :expanded="runExpanded"
          :style="{height: bottomHeight + 'px'}" @expand="runExpanded = !runExpanded"/>
      </section>
    </div>
  </div>
</template>

<style scoped src="./file-workspace.css"></style>
<style scoped>
.docker-hint{margin:18px 0;padding:10px 14px;border:1px solid var(--vp-c-divider);border-radius:7px}
.docker-hint summary{cursor:pointer;color:var(--vp-c-text-2)}
.docker-action{padding:5px 8px;border-radius:5px;color:var(--lab-blue);background:var(--lab-blue-soft);font-size:13px}
</style>
