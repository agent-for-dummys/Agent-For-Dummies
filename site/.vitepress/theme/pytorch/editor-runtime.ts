// Cache one editor runtime for all lessons and warm it before changing pages.
let runtime: Promise<any[]> | undefined;
export function loadEditorRuntime() {
  return runtime ??= Promise.all([import('codemirror'), import('@codemirror/lang-python'), import('@codemirror/view'), import('@codemirror/commands'), import('@codemirror/state'), import('@codemirror/language'), import('@lezer/highlight')]);
}
export async function prepareLearningPage() {
  await Promise.all([loadEditorRuntime(), document.fonts.load('14px "PyTorch Mono"').catch(() => []), document.fonts.load('14px "PyTorch Digits"', '0123456789').catch(() => [])]);
}
