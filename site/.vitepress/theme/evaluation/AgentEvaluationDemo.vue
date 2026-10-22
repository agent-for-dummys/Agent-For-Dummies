<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, ref, useId, watch} from 'vue';
import {createRun, question, scenarios, steps, type ScenarioId} from './weather-evaluation';

const root = ref<HTMLElement>();
const scenario = ref<ScenarioId>('success');
const step = ref(0), reached = ref(0), repaired = ref(false);
const picker = ref<HTMLElement>(), pickerButton = ref<HTMLButtonElement>();
const menuOpen = ref(false), menuId = useId();
const scenarioLabel = computed(() => scenarios.find(item => item.id === scenario.value)!.label);
const run = computed(() => createRun(scenario.value, repaired.value));
const assessed = computed(() => reached.value === steps.length - 1);
const passed = computed(() => run.value.checks.every(check => check.passed));
function stepFailed(index: number) {
  return assessed.value && (index === 4 ? !passed.value : run.value.checks.some(check => !check.passed && check.step === index));
}
function stepPassed(index: number) {
  return (index < reached.value || assessed.value && index === 4)
    && !stepFailed(index) && !(scenario.value === 'timeout' && index === 2);
}
function go(index: number) {
  step.value = Math.max(0, Math.min(steps.length - 1, index));
  reached.value = Math.max(reached.value, step.value);
}
function restart() { repaired.value = false; step.value = 0; reached.value = 0; }
function repair() {
  const target = run.value.diagnosis?.step || 1;
  repaired.value = true;
  step.value = target;
  reached.value = target;
}
function keyboard(event: KeyboardEvent) {
  if (event.target !== event.currentTarget) return;
  if (event.key === 'ArrowRight') { event.preventDefault(); go(step.value + 1); }
  if (event.key === 'ArrowLeft') { event.preventDefault(); go(step.value - 1); }
}
async function openMenu(index = scenarios.findIndex(item => item.id === scenario.value)) {
  menuOpen.value = true;
  await nextTick();
  picker.value?.querySelectorAll<HTMLButtonElement>('[role="menuitemradio"]')[index]?.focus();
}
function closeMenu(restoreFocus = false) {
  menuOpen.value = false;
  if (restoreFocus) pickerButton.value?.focus({preventScroll: true});
}
function selectScenario(id: ScenarioId) { scenario.value = id; closeMenu(true); }
function menuKeyboard(event: KeyboardEvent) {
  const items = [...(picker.value?.querySelectorAll<HTMLButtonElement>('[role="menuitemradio"]') || [])];
  const index = items.indexOf(document.activeElement as HTMLButtonElement);
  let next: number | undefined;
  if (event.key === 'ArrowDown') next = (index + 1) % items.length;
  if (event.key === 'ArrowUp') next = (index - 1 + items.length) % items.length;
  if (event.key === 'Home') next = 0;
  if (event.key === 'End') next = items.length - 1;
  if (next !== undefined) { event.preventDefault(); items[next]?.focus(); }
  if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeMenu(true); }
}
function outsideClick(event: PointerEvent) { if (!picker.value?.contains(event.target as Node)) closeMenu(); }
function pickerBlur(event: FocusEvent) { if (!picker.value?.contains(event.relatedTarget as Node | null)) closeMenu(); }
watch(scenario, restart);
onMounted(() => document.addEventListener('pointerdown', outsideClick));
onUnmounted(() => document.removeEventListener('pointerdown', outsideClick));
</script>

<template>
  <section ref="root" class="agent-eval-demo" :data-scenario="scenario" :data-step="step" :data-repaired="repaired" aria-label="Agent 评测交互演示" tabindex="0" @keydown="keyboard">
    <header class="demo-chrome">
      <div class="window-dots" aria-hidden="true"><i/><i/><i/></div>
      <span class="window-title">天气查询</span>
      <div ref="picker" class="scenario-picker" @focusout="pickerBlur">
        <button ref="pickerButton" type="button" class="scenario-trigger" aria-label="选择评测场景" aria-haspopup="menu" :aria-expanded="menuOpen" :aria-controls="menuId" @click="menuOpen?closeMenu():openMenu()" @keydown.down.prevent="openMenu(0)" @keydown.up.prevent="openMenu(scenarios.length-1)"><span>{{scenarioLabel}}</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m5 6 3 3 3-3"/></svg></button>
        <div v-if="menuOpen" :id="menuId" class="scenario-menu" role="menu" aria-label="评测场景" @keydown="menuKeyboard">
          <button v-for="item in scenarios" :key="item.id" type="button" role="menuitemradio" :aria-checked="scenario===item.id" class="scenario-option" @click="selectScenario(item.id)"><span>{{item.label}}</span></button>
        </div>
      </div>
    </header>

    <div class="execution-body">
      <nav class="trace-timeline" aria-label="执行记录 Trace">
        <span class="trace-label">Trace</span>
        <ol>
          <li v-for="(item,index) in steps" :key="item.kind">
            <button type="button" class="trace-node" :class="{active:step===index,complete:stepPassed(index),fault:stepFailed(index),warning:scenario==='timeout'&&index===2&&reached>=2}" :disabled="index>reached" :aria-current="step===index?'step':undefined" :aria-label="`查看${item.title}`" @click="go(index)">
              <span class="trace-dot">
                <svg v-if="stepFailed(index)" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 4v5m0 3h.01"/></svg>
                <svg v-else-if="scenario==='timeout'&&index===2&&reached>=2" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 4v4l2 1"/></svg>
                <span v-else>{{String(index+1).padStart(2,'0')}}</span>
              </span>
              <span>{{item.title}}</span>
            </button>
          </li>
        </ol>
      </nav>

      <div class="step-inspector" aria-live="polite" aria-atomic="true">
        <Transition name="eval-stage" mode="out-in">
          <div :key="`${scenario}:${step}:${repaired}`" class="step-content">
            <div class="step-heading"><h3>{{steps[step].title}}</h3><span v-if="repaired" class="repaired-tag">修复后</span></div>

            <template v-if="step===0">
              <div class="message-card user-message"><span class="message-author">用户</span><p>{{question}}</p></div>
              <div class="fixture-note"><span class="fixture-dot"/>{{scenario==='timeout'?'测试条件：天气接口请求超时':'固定测试数据：杭州 · 小雨 · 18℃'}}</div>
            </template>

            <template v-else-if="step===1">
              <div class="request-context"><span>用户指定城市</span><strong>杭州</strong></div>
              <pre class="call-code">get_weather(
    city=<mark :class="{'value-error':assessed&&run.city!=='杭州'}">"{{run.city}}"</mark>
)</pre>
              <p v-if="assessed&&run.city!=='杭州'" class="inline-error"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 4v5m0 3h.01"/><circle cx="8" cy="8" r="6.5"/></svg>用户输入杭州，工具却查询了北京。</p>
              <p v-else-if="repaired&&scenario==='wrong-city'" class="inline-success">city 已改回用户指定的杭州。</p>
            </template>

            <template v-else-if="step===2">
              <div v-if="!run.weather" class="timeout-card"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/></svg><strong>TimeoutError</strong><span>天气服务请求超时，没有返回天气数据。</span></div>
              <div v-else class="weather-card" :class="{'evidence-error':assessed&&run.city!=='杭州'}">
                <div class="weather-place"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M15.5 8c0 4-5.5 9-5.5 9S4.5 12 4.5 8a5.5 5.5 0 0 1 11 0Z"/><circle cx="10" cy="8" r="1.7"/></svg>{{run.weather.city}}</div>
                <strong class="temperature">{{run.weather.temperature}}<span>℃</span></strong>
                <div class="weather-condition"><svg v-if="run.weather.condition==='小雨'" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 21H8a5 5 0 0 1 0-10 8 8 0 0 1 15-1 5.5 5.5 0 0 1 1 11h-1M11 25l-1 3m7-3-1 3m7-3-1 3"/></svg><svg v-else viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="6"/><path d="M16 3v3m0 20v3M3 16h3m20 0h3M7 7l2 2m14 14 2 2M7 25l2-2M23 9l2-2"/></svg><span>{{run.weather.condition}}</span></div>
              </div>
              <p v-if="run.weather&&assessed&&run.city!=='杭州'" class="evidence-note">天气服务正常执行了请求，返回的是北京的数据。</p>
            </template>

            <template v-else-if="step===3">
              <div class="message-card agent-message" :class="{'evidence-error':assessed&&run.diagnosis?.step===3}"><span class="message-author">Agent</span><p>{{run.answer}}</p></div>
              <div v-if="scenario==='wrong-answer'" class="temperature-comparison"><div><span>工具温度</span><strong>18℃</strong></div><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 10h14m-5-5 5 5-5 5"/></svg><div :class="{mismatch:!repaired}"><span>回答温度</span><strong>{{repaired?18:28}}℃</strong></div></div>
              <p v-if="scenario==='timeout'" class="evidence-note">工具返回：TimeoutError，未取得天气数据。</p>
            </template>

            <template v-else>
              <div class="evaluation-verdict" :class="passed?'passed':'failed'"><strong>{{passed?'Passed':'Failed'}}</strong></div>
              <ul class="rubric-list">
                <li v-for="check in run.checks" :key="check.label" :class="check.passed?'check-passed':'check-failed'">
                  <button type="button" :aria-label="`${check.label}：${check.passed?'Passed':'Failed'}，查看对应步骤`" @click="go(check.step)"><span>{{check.label}}</span><small>{{check.passed?'Passed':'Failed'}}</small></button>
                  <p v-if="!check.passed">{{check.evidence}}</p>
                </li>
              </ul>
              <p v-if="scenario==='timeout'&&passed&&!run.queryCompleted" class="incomplete-note">未取得天气数据。</p>
            </template>
          </div>
        </Transition>
      </div>
    </div>

    <div v-if="assessed&&run.diagnosis" class="diagnosis" role="note" aria-label="错误定位">
      <button type="button" class="diagnosis-target" @click="go(run.diagnosis.step)"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6"/><circle cx="10" cy="10" r="2"/><path d="M10 2v2m0 12v2M2 10h2m12 0h2"/></svg><span>{{run.diagnosis.title}}</span><svg class="jump-arrow" viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h12m-5-5 5 5-5 5"/></svg></button>
      <p>{{run.diagnosis.reason}}</p>
      <div class="repair-row"><p>{{run.diagnosis.fix}}</p><button type="button" class="repair-button" @click="repair">查看修复<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10m-4-4 4 4-4 4"/></svg></button></div>
    </div>

    <footer class="demo-controls">
        <button type="button" class="icon-button" :disabled="step===0" aria-label="上一步" @click="go(step-1)"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12 5-5 5 5 5"/></svg></button>
        <button type="button" class="icon-button" :disabled="step===4" aria-label="下一步" @click="go(step+1)"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m8 5 5 5-5 5"/></svg></button>
    </footer>
  </section>
</template>

<style scoped>
.agent-eval-demo{--eval-blue:#1686bd;--eval-blue-soft:#eef7fd;--eval-success:var(--eval-blue);--eval-success-soft:var(--eval-blue-soft);--eval-red:#b84c59;--eval-red-soft:#fcf2f3;--eval-amber:#a77524;--eval-amber-soft:#f9f5ec;--eval-line:#e6e9ed;--eval-panel:#f8f9fb;--eval-bg:#fff;--eval-text:#303943;--eval-secondary:#747d88;position:relative;overflow:hidden;margin:26px 0 32px;border:1px solid var(--eval-line);border-radius:14px;background:var(--eval-bg);color:var(--eval-text);box-shadow:0 3px 8px #202f4103,0 16px 40px -20px #202f4124;font-family:var(--vp-font-family-base);font-size:13px;line-height:1.6;isolation:isolate}
.agent-eval-demo button{font:inherit;cursor:pointer;outline-offset:3px}
.agent-eval-demo button{margin:0}
.agent-eval-demo button:disabled{cursor:default;opacity:.35}
.agent-eval-demo button:focus-visible,.agent-eval-demo:focus-visible{outline:2px solid var(--eval-blue);outline-offset:-3px}
.agent-eval-demo svg{width:18px;height:18px;flex:none;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.demo-chrome{display:flex;align-items:center;gap:12px;padding:12px 15px;min-height:53px;border-bottom:1px solid var(--eval-line);background:var(--eval-panel)}
.window-dots{display:flex;gap:5px;flex:none}
.window-dots i{width:8px;height:8px;border:1px solid #d2d7de;border-radius:50%;background:#e2e5e9}
.window-dots i:first-child{background:#f3b8b3;border-color:#eaa8a2}.window-dots i:nth-child(2){background:#f0d495;border-color:#e5c781}.window-dots i:last-child{background:#b3d6b8;border-color:#a2c9a9}
.window-title{font-size:12px;font-weight:550;letter-spacing:.1px;margin-right:auto}
.scenario-picker{position:relative;display:flex;align-items:center;z-index:5}
.scenario-trigger{display:flex;align-items:center;gap:16px;min-width:120px;justify-content:space-between;padding:5px 9px 5px 11px;border:1px solid var(--eval-line);border-radius:7px;background:var(--eval-bg);box-shadow:0 1px 2px #26374c08;color:var(--eval-text);font-size:12px!important;line-height:20px}
.scenario-trigger:hover{border-color:#c1cbd5}
.scenario-trigger[aria-expanded=true]{border-color:#a6c6db;box-shadow:0 0 0 2px #1686bd12}
.scenario-trigger svg{width:13px;height:13px;color:var(--eval-secondary)}
.scenario-menu{position:absolute;right:0;top:calc(100% + 6px);z-index:10;min-width:182px;padding:5px;border:1px solid #dce2e9;border-radius:10px;background:#ffffffed;box-shadow:0 6px 12px #1d2d4412,0 18px 40px -10px #1d2d4438;backdrop-filter:blur(20px)}
.scenario-option{display:flex;align-items:center;gap:9px;width:100%;padding:7px 9px;border-radius:6px;font-size:12px!important;line-height:20px;text-align:left;white-space:nowrap;color:var(--eval-text)}
.scenario-option[aria-checked=true],.scenario-option:hover,.scenario-option:focus-visible{background:#1686bd;color:#fff;outline:none!important}
.dark .scenario-menu{border-color:#4a515d;background:#2c323cee;box-shadow:0 10px 35px #0006}
.agent-eval-demo .incomplete-note{margin:15px 0 0;font-size:11px;line-height:1.8;color:var(--eval-amber)}
.execution-body{display:grid;grid-template-columns:148px minmax(0,1fr);min-height:350px}
.trace-timeline{padding:22px 10px 22px 12px;background:var(--eval-panel);border-right:1px solid var(--eval-line)}
.trace-label{display:block;margin:0 0 13px 10px;color:var(--eval-secondary);font:11px var(--vp-font-family-mono);letter-spacing:.3px}
.trace-timeline ol{position:relative;list-style:none;margin:0;padding:0;display:grid;gap:13px}
.trace-timeline ol:before{position:absolute;content:'';left:20px;top:22px;bottom:22px;width:1px;background:var(--eval-line)}
.trace-timeline li{position:relative;margin:0;padding:0;list-style:none}
.trace-node{position:relative;display:flex;align-items:center;gap:9px;width:100%;padding:8px 9px;text-align:left;color:var(--eval-secondary);border:1px solid transparent;border-radius:8px;font-size:12px!important;white-space:nowrap;transition:background .18s,color .18s}
.trace-node.active{background:var(--eval-bg);border-color:var(--eval-line);color:var(--eval-blue);box-shadow:0 2px 4px #20334704}
.trace-node.fault{color:var(--eval-red)}
.trace-node.fault.active{border-color:#edcdd2;background:var(--eval-red-soft)}
.trace-dot{position:relative;display:grid;place-items:center;width:22px;height:22px;flex:none;border:1px solid var(--eval-line);border-radius:50%;background:var(--eval-panel);font:9px var(--vp-font-family-mono);color:var(--eval-secondary);z-index:1}
.trace-dot svg{width:13px;height:13px}
.trace-node.active .trace-dot{border-color:var(--eval-blue);background:var(--eval-blue);color:#fff}
.trace-node.fault .trace-dot{border-color:#e4b5bf;color:var(--eval-red);background:var(--eval-red-soft)}
.trace-node.complete{color:var(--eval-success)}
.trace-node.complete .trace-dot{border-color:#bed9e9;background:var(--eval-success-soft);color:var(--eval-success)}
.trace-node.complete.active .trace-dot{background:var(--eval-success);border-color:var(--eval-success);color:var(--eval-bg)}
.trace-node.warning .trace-dot{border-color:#e4d2ac;color:var(--eval-amber);background:var(--eval-amber-soft)}
.step-inspector{min-width:0;padding:25px 25px 22px}
.step-heading{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.agent-eval-demo .step-heading h3{margin:0;padding:0;border:0;font-size:16px;line-height:24px;letter-spacing:0;font-weight:600;color:var(--eval-text)}
.repaired-tag{padding:2px 6px;border-radius:4px;background:var(--eval-success-soft);color:var(--eval-success);font-size:10px}
.message-card{padding:16px 18px;border:1px solid var(--eval-line);border-radius:10px;background:var(--eval-panel)}
.message-author{font-size:10px;letter-spacing:.2px;color:var(--eval-secondary)}
.agent-eval-demo .message-card p{margin:9px 0 0;font-size:13px;line-height:1.95;overflow-wrap:anywhere}
.user-message{background:var(--eval-blue-soft);border-color:#dfedf7}
.fixture-note{display:flex;align-items:center;gap:6px;margin-top:18px;font-size:10px;color:var(--eval-secondary)}
.fixture-dot{width:4px;height:4px;background:#a8b2bd;border-radius:50%;flex:none}
.request-context{display:flex;align-items:center;gap:12px;margin-bottom:13px;font-size:11px;color:var(--eval-secondary)}
.request-context strong{font-size:12px;font-weight:500;color:var(--eval-text)}
.agent-eval-demo .call-code{padding:20px;margin:0;border:1px solid var(--eval-line);border-radius:9px;background:var(--eval-panel);color:var(--eval-text);font:13px/2 var(--vp-font-family-mono);white-space:pre-wrap;overflow-wrap:anywhere}
.call-code mark{background:transparent;color:#397552;padding:2px 3px;border-radius:3px}
.call-code .value-error{color:var(--eval-red);background:#f6dce1;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:4px}
.agent-eval-demo .inline-error,.agent-eval-demo .inline-success{display:flex;align-items:center;gap:6px;margin:13px 0 0;font-size:11px;line-height:1.8;color:var(--eval-red)}
.inline-error svg{width:15px;height:15px}.agent-eval-demo .inline-success{color:var(--eval-success)}
.weather-card{display:grid;grid-template-columns:1fr auto;align-items:center;gap:17px;padding:22px;border:1px solid var(--eval-line);border-radius:10px;background:var(--eval-panel)}
.weather-place{display:flex;align-items:center;gap:6px;grid-column:1/-1;font-size:13px;color:var(--eval-secondary)}
.weather-place svg{width:15px;height:15px}
.temperature{font-size:43px;line-height:1.2;font-weight:450;letter-spacing:-1.5px;font-variant-numeric:tabular-nums}
.temperature>span{margin-left:6px;font-size:21px;font-weight:400;letter-spacing:0;color:var(--eval-secondary)}
.weather-condition{display:flex;align-items:center;gap:11px;font-size:13px;color:var(--eval-secondary)}
.weather-condition svg{width:31px;height:31px;stroke-width:1.4}
.timeout-card{display:flex;flex-direction:column;align-items:center;gap:13px;padding:24px 18px;border:1px solid #e8ddc5;border-radius:10px;background:var(--eval-amber-soft);color:var(--eval-amber)}
.timeout-card>svg{width:27px;height:27px}.timeout-card strong{font:13px var(--vp-font-family-mono)}.timeout-card>span{font-size:11px;text-align:center}
.agent-eval-demo .evidence-note{margin:15px 0 0;color:var(--eval-secondary);font-size:11px;line-height:1.8}
.evidence-error{border-color:#e4bcc4;background:var(--eval-red-soft)}
.temperature-comparison{display:flex;align-items:center;justify-content:space-between;gap:15px;margin:20px 3px 0}
.temperature-comparison>div{display:flex;flex-direction:column;gap:5px}
.temperature-comparison span{font-size:10px;color:var(--eval-secondary)}
.temperature-comparison strong{font:500 17px var(--vp-font-family-mono);color:var(--eval-text)}
.temperature-comparison>svg{color:#b1bac3}.temperature-comparison .mismatch strong{color:var(--eval-red)}
.evaluation-verdict{display:flex;align-items:center;gap:9px;margin:0 0 15px}
.evaluation-verdict strong{font-size:20px;line-height:28px;font-weight:600}
.passed{color:var(--eval-success)}.failed{color:var(--eval-red)}
.agent-eval-demo .rubric-list{list-style:none;padding:0;margin:0}
.agent-eval-demo .rubric-list li{list-style:none;padding:0;margin:0;border-bottom:1px solid var(--eval-line)}
.rubric-list button{display:flex;align-items:flex-start;gap:7px;width:100%;padding:11px 0;text-align:left;font-size:11px!important;line-height:18px;color:var(--eval-text)}
.rubric-list button:hover{color:var(--eval-blue)}
.rubric-list button>span{flex:1}
.rubric-list small{font-size:10px;line-height:18px;color:var(--eval-secondary)}
.check-passed small{color:var(--eval-success)}.check-failed small{color:var(--eval-red)}
.agent-eval-demo .rubric-list li>p{margin:-3px 0 11px;color:var(--eval-red);font-size:10px;line-height:1.8}
.diagnosis{padding:17px 22px;border-top:1px solid #efdadf;background:var(--eval-red-soft)}
.diagnosis-target{display:flex;align-items:center;gap:7px;width:100%;text-align:left;color:var(--eval-red);font-size:12px!important;font-weight:550!important}
.diagnosis-target>svg{width:16px;height:16px}.diagnosis-target .jump-arrow{margin-left:auto}
.agent-eval-demo .diagnosis p{margin:9px 0 0;font-size:11px;line-height:1.85;color:var(--eval-secondary)}
.repair-row{display:flex;align-items:flex-end;gap:18px}
.repair-row>p{flex:1}
.repair-button{display:flex;align-items:center;gap:6px;flex:none;padding:6px 9px;border:1px solid #e3cbd1;border-radius:6px;background:var(--eval-bg);font-size:11px!important;color:var(--eval-red);white-space:nowrap}
.repair-button svg{width:12px;height:12px}
.demo-controls{display:flex;justify-content:center;align-items:center;gap:26px;padding:12px 16px;border-top:1px solid var(--eval-line)}
.icon-button{display:grid;place-items:center;width:26px;height:29px;border-radius:5px;color:var(--eval-secondary)}
.icon-button:hover:not(:disabled){background:var(--eval-panel);color:var(--eval-blue)}
.icon-button svg{width:15px;height:15px}
.eval-stage-enter-active,.eval-stage-leave-active{transition:opacity .16s,translate .16s}
.eval-stage-enter-from{opacity:0;translate:0 5px}.eval-stage-leave-to{opacity:0;translate:0 -4px}
.dark .agent-eval-demo{--eval-blue:#83bddc;--eval-blue-soft:#243846;--eval-red:#e0939f;--eval-red-soft:#32292e;--eval-amber:#d0b47e;--eval-amber-soft:#332f26;--eval-line:#363e47;--eval-panel:#262b32;--eval-bg:#20252b;--eval-text:#dee4ec;--eval-secondary:#a0a9b5;box-shadow:0 12px 35px -20px #0008}
.dark .trace-node.complete .trace-dot{border-color:#476879}.dark .trace-node.active .trace-dot{color:#192a36}.dark .trace-node.fault .trace-dot{border-color:#77515d;color:var(--eval-red)}
.dark .user-message{border-color:#3b5364}.dark .call-code mark{color:#a2c4a9}.dark .call-code .value-error{color:var(--eval-red);background:#53303c}
.dark .timeout-card{border-color:#5a4d35}.dark .evidence-error{border-color:#76515c}.dark .diagnosis{border-color:#523a44}.dark .repair-button{border-color:#65434f}
@media(max-width:620px){.demo-chrome{padding:11px 12px;gap:9px}.window-dots{gap:4px}.window-dots i{width:7px;height:7px}.window-title{font-size:11px}.scenario-trigger{max-width:150px;font-size:11px!important}.execution-body{grid-template-columns:1fr;min-height:0}.trace-timeline{border-right:0;border-bottom:1px solid var(--eval-line);padding:11px 10px}.trace-label{display:none}.trace-timeline ol{display:flex;gap:4px;justify-content:space-between}.trace-timeline ol:before{top:17px;bottom:auto;left:8%;right:8%;width:auto;height:1px}.trace-timeline li{flex:1;min-width:0}.trace-node{flex-direction:column;gap:5px;padding:4px 1px;font-size:10px!important;white-space:normal;text-align:center}.trace-node.active{box-shadow:none}.trace-dot{width:22px;height:22px}.step-inspector{padding:20px;min-height:320px}.diagnosis{padding:16px 18px}.repair-row{flex-direction:column;align-items:flex-start;gap:12px}.repair-button{align-self:flex-end}.demo-controls{padding:10px 11px;gap:26px}}
@media(prefers-reduced-motion:reduce){.trace-node,.eval-stage-enter-active,.eval-stage-leave-active{transition:none}}
</style>
