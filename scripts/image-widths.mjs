// Accept the note editor's ![description|420](image.png) width convention.
// Operate on parsed image tokens so fenced code and other pipe characters stay intact.
export function imageWidths(md) {
  md.core.ruler.after('inline', 'image_widths', state => {
    function visit(tokens) {
      for (const token of tokens) {
        if (token.type === 'image') {
          const match = token.content.match(/^(.*)\|([1-9]\d{0,3})$/s);
          if (!match) continue;
          const width = Number(match[2]);
          token.content = match[1].trim();
          token.children = [];
          md.inline.parse(token.content, md, state.env, token.children);
          token.attrSet('width', String(width));
          const previous = token.attrGet('style')?.trim() || '';
          token.attrSet('style', `${previous}${previous && !previous.endsWith(';') ? ';' : ''}width:${width}px;max-width:100%;height:auto;`);
        } else if (token.children) visit(token.children);
      }
    }
    visit(state.tokens);
  });
}
