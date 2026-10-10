// Render the note's Obsidian Hessian callouts without enabling raw HTML.
export function hessianCallouts(md) {
  md.core.ruler.after('inline', 'hessian_callouts', state => {
    const tokens = state.tokens;
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type !== 'blockquote_open') continue;
      const header = tokens[i + 2];
      const match = header?.type === 'inline' && header.content.match(/^\[!hessian\]\s+([^\n]+)$/i);
      if (!match || tokens[i + 1]?.type !== 'paragraph_open') continue;

      let depth = 1;
      let end = i + 1;
      for (; end < tokens.length; end++) {
        if (tokens[end].type === 'blockquote_open') depth++;
        if (tokens[end].type === 'blockquote_close' && --depth === 0) break;
      }
      if (end === tokens.length) continue;

      tokens[i].tag = 'section';
      tokens[i].attrSet('class', 'callout');
      tokens[i].attrSet('data-callout', 'hessian');
      tokens[end].tag = 'section';
      tokens[i + 1].attrSet('class', 'callout-title');
      header.content = match[1];
      header.children = [];
      md.inline.parse(header.content, md, state.env, header.children);

      for (let j = i + 4; j < end; j++) {
        for (const image of tokens[j].children || []) {
          if (image.type !== 'image') continue;
          image.content = image.content.replace(/\|\d+(?:x\d+)?$/, '');
          image.children = [];
          md.inline.parse(image.content, md, state.env, image.children);
        }
      }

      const contentOpen = new state.Token('hessian_content_open', 'div', 1);
      contentOpen.attrSet('class', 'callout-content');
      const contentClose = new state.Token('hessian_content_close', 'div', -1);
      tokens.splice(end, 0, contentClose);
      tokens.splice(i + 4, 0, contentOpen);
      i = end + 2;
    }
  });
}
