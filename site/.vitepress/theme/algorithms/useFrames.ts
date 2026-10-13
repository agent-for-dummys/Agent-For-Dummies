import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

export function useFrames(options: {
  count: () => number; reset: () => unknown; active: () => boolean;
  paused: () => boolean; reducedMotion: () => boolean; speed: () => number;
}) {
  const frame = ref(0);
  const complete = computed(() => frame.value >= options.count());
  const duration = computed(() => 3600 / (options.speed() * options.count()));
  let timer: ReturnType<typeof setTimeout> | undefined;
  let mounted = false;
  function queue() {
    clearTimeout(timer);
    if (!mounted || complete.value || !options.active() || options.paused() || options.reducedMotion()) return;
    timer = setTimeout(() => { frame.value++; queue(); }, duration.value);
  }
  function reset() { frame.value = options.reducedMotion() ? options.count() : 0; queue(); }
  watch(options.reset, reset);
  watch(() => [options.active(), options.paused(), options.speed()], queue);
  watch(options.reducedMotion, reset);
  onMounted(() => { mounted = true; reset(); });
  onUnmounted(() => { mounted = false; clearTimeout(timer); });
  return { frame, complete, duration };
}
