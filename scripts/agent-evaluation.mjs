export function agentEvaluation(md) {
  md.block.ruler.before('fence', 'agent_evaluation', (state, start, end, silent) => {
    const line = state.src.slice(state.bMarks[start] + state.tShift[start], state.eMarks[start]);
    if (line.trim() !== '::: agent-evaluation' || start + 1 >= end) return false;
    const close = state.src.slice(state.bMarks[start + 1] + state.tShift[start + 1], state.eMarks[start + 1]);
    if (close.trim() !== ':::') return false;
    if (silent) return true;
    const token = state.push('agent_evaluation', '', 0);
    token.block = true;
    token.map = [start, start + 2];
    state.line = start + 2;
    return true;
  }, {alt: ['paragraph', 'reference', 'blockquote', 'list']});
  md.renderer.rules.agent_evaluation = () => '<AgentEvaluationDemo />\n';
}
