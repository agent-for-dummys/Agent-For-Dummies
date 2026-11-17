<script setup lang="ts">
import {computed} from 'vue';
import {withBase} from 'vitepress';
import {dockerTasks, expectedOutput} from './pytorch/docker-course';

const props = defineProps<{level: 1 | 2}>();
const task = computed(() => dockerTasks[props.level - 1]);
const href = computed(() => withBase('/practice?course=development&task=' + encodeURIComponent(task.value.id)));
</script>

<template>
  <section class="practice-card" :aria-label="task.title">
    <header class="practice-card-header">
      <span class="practice-card-label">题目描述</span>
      <a :href="href" class="practice-card-link" :aria-label="'做题：' + task.title">
        做题 <span aria-hidden="true">→</span>
      </a>
    </header>
    <div class="practice-card-content">
      <strong>{{ task.title }}</strong>
      <template v-if="level === 1">
        <p>你拿到一个小型 C++ 项目，里面有 <code>main.cpp</code> 和写好的 <code>Makefile</code>。现在给它补一份 <code>dockerfile</code>，让别人拿到项目后也能用 Docker 编译和运行。</p>
        <p>以 <code>ubuntu:24.04</code> 为基础镜像，把编译工具和项目文件放进去。构建时用 <code>make</code> 生成 <code>hello</code>，容器启动时执行它。</p>
        <p><strong>验收</strong>　运行 <code>coder:step1</code>，终端应输出这一行：</p>
        <pre class="practice-card-output"><code>{{ expectedOutput }}</code></pre>
      </template>
      <template v-else>
        <p>第一关的镜像里已经能运行程序，编译工具和源码也还在里面。现在沿用你写的 <code>dockerfile</code>，试着把镜像缩小。</p>
        <p>把编译和运行拆成两个阶段。让 <code>make</code> 生成静态链接的 <code>hello</code>，再把它复制到基于 <code>scratch</code> 的运行阶段。</p>
        <p><strong>验收</strong>　运行 <code>coder:step2</code>，确认输出与第一关相同。再执行 <code>docker image ls coder</code>，看看第二关的镜像小了多少。</p>
      </template>
    </div>
  </section>
</template>

<style scoped>
.practice-card {
  margin: 24px 0;
  overflow: hidden;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  background: var(--vp-c-bg);
}
.practice-card-header {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  border-bottom: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
}
.practice-card-label {
  display: flex;
  align-items: center;
  padding: 10px 0 8px;
  border-bottom: 2px solid var(--vp-button-brand-bg);
  color: var(--vp-c-text-1);
  font-size: 14px;
  font-weight: 500;
}
.practice-card a.practice-card-link {
  align-self: center;
  margin: 6px 0;
  padding: 6px 11px;
  border: 0;
  border-radius: 7px;
  background: var(--vp-button-brand-bg);
  color: var(--vp-button-brand-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  text-decoration: none;
  white-space: nowrap;
}
.practice-card a.practice-card-link:hover {
  background: var(--vp-button-brand-hover-bg);
  color: var(--vp-button-brand-hover-text);
}
.practice-card a.practice-card-link:focus-visible {
  outline: 2px solid var(--vp-button-brand-bg);
  outline-offset: 2px;
}
.practice-card-content { padding: 16px; }
.practice-card-content > strong { font-size: 17px; }
.practice-card-content p { margin: 10px 0 0; color: var(--vp-c-text-2); }
.practice-card-output {
  margin: 8px 0 0;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--vp-code-bg);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.practice-card-output code { padding: 0; }
</style>
