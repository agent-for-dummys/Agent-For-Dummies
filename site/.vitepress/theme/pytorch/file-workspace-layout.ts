import {ref} from 'vue';

export function useFileWorkspaceLayout() {
  const splitter = ref<HTMLElement>();
  const codePane = ref<HTMLElement>();
  const split = ref(.5);
  const bottomHeight = ref(240);
  const runExpanded = ref(false);
  let startRatio = split.value;
  let startHeight = bottomHeight.value;

  function setSplit(ratio: number) {
    split.value = Math.min(.7, Math.max(.25, ratio));
  }

  function setHeight(height: number) {
    bottomHeight.value = Math.min((codePane.value?.clientHeight || 700) - 160, Math.max(48, height));
  }

  return {
    splitter, codePane, split, bottomHeight, runExpanded,
    startSplit: () => { startRatio = split.value; },
    dragSplit: (distance: number) => setSplit(startRatio + distance / (splitter.value?.clientWidth || 1000)),
    stepSplit: (direction: number) => setSplit(split.value + direction * .03),
    startHeight: () => { startHeight = bottomHeight.value; },
    dragHeight: (distance: number) => setHeight(startHeight + distance),
    stepHeight: (direction: number) => setHeight(bottomHeight.value + direction * 25),
  };
}
