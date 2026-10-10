// Reuse the existing MathJax renderer for the notes' \( ... \) syntax.
// Parsing as an inline rule keeps code spans and fenced code unchanged.
export function parenthesizedMath(md) {
  md.inline.ruler.before('escape', 'parenthesized_math', (state, silent) => {
    const start = state.pos;
    if (!state.src.startsWith('\\(', start)) return false;
    for (let end = start + 2; end < state.posMax - 1; end++) {
      if (!state.src.startsWith('\\)', end)) continue;
      let preceding = 0;
      for (let i = end - 1; i >= start + 2 && state.src[i] === '\\'; i--) preceding++;
      if (preceding % 2) continue;
      if (!silent) {
        const token = state.push('math_inline', 'math', 0);
        token.content = state.src.slice(start + 2, end).trim();
        token.markup = '\\(';
      }
      state.pos = end + 2;
      return true;
    }
    return false;
  });
}
