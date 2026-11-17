export function dockerPracticeCards(md) {
  md.block.ruler.before('fence', 'docker_practice_card', (state, start, end, silent) => {
    const line = index => state.src.slice(state.bMarks[index] + state.tShift[index], state.eMarks[index]).trim();
    const match = /^::: docker-practice ([12])$/.exec(line(start));
    if (!match || start + 1 >= end || line(start + 1) !== ':::') return false;
    if (silent) return true;

    const token = state.push('docker_practice_card', '', 0);
    token.block = true;
    token.map = [start, start + 2];
    token.content = match[1];
    state.line = start + 2;
    return true;
  }, { alt: ['paragraph', 'reference', 'blockquote', 'list'] });

  md.renderer.rules.docker_practice_card = (tokens, index) =>
    `<DockerPracticeCard :level="${tokens[index].content}" />\n`;
}
