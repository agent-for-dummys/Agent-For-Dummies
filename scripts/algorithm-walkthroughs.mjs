// A deliberately narrow Markdown block: no arbitrary HTML needs to be enabled.
export function algorithmWalkthroughs(md) {
  md.block.ruler.before('fence', 'algorithm_walkthrough', (state, start, end, silent) => {
    const line = state.src.slice(state.bMarks[start] + state.tShift[start], state.eMarks[start]);
    const match = line.match(/^::: algorithm (attention|multi-head|transformer|mask|padding)\s*$/);
    if (!match || start + 1 >= end) return false;
    const close = state.src.slice(state.bMarks[start + 1] + state.tShift[start + 1], state.eMarks[start + 1]);
    if (close.trim() !== ':::') return false;
    if (silent) return true;
    const token = state.push('algorithm_walkthrough', '', 0);
    token.block = true;
    token.map = [start, start + 2];
    token.content = match[1];
    state.line = start + 2;
    return true;
  }, { alt: ['paragraph', 'reference', 'blockquote', 'list'] });
  md.renderer.rules.algorithm_walkthrough = (tokens, index) => `<AlgorithmWalkthrough kind="${tokens[index].content}" />\n`;
}
