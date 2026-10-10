import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { createMarkdownRenderer } from 'vitepress';
import { root, markdownHeadingSlug } from './sync-content.mjs';

async function markdownFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const lists = await Promise.all(entries.map(entry => {
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? markdownFiles(file) : entry.name.endsWith('.md') ? [file] : [];
  }));
  return lists.flat();
}

const files = [
  ...(await markdownFiles(path.join(root, 'docs'))),
  ...(await readdir(root)).filter(name => name.endsWith('.md')).map(name => path.join(root, name))
];
const renderer = await createMarkdownRenderer(path.join(root, 'site'));
const notes = new Map();
for (const file of files) {
  const source = await readFile(file, 'utf8');
  const tokens = renderer.parse(source, {});
  const anchors = new Set();
  const counts = new Map();
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].type !== 'heading_open') continue;
    const title = tokens[i + 1].children.filter(token => token.type === 'text' || token.type === 'code_inline').map(token => token.content).join('');
    const slug = markdownHeadingSlug(title);
    const count = counts.get(slug) || 0;
    counts.set(slug, count + 1);
    anchors.add(count ? `${slug}-${count}` : slug);
  }
  notes.set(file, { tokens, anchors });
}

const errors = [];
let images = 0;
let links = 0;
async function check(file, kind, raw) {
  const target = decodeURIComponent(raw);
  const label = path.relative(root, file);
  if (kind === 'image') {
    images++;
    if (/^(?:[a-z][a-z\d+.-]*:|\/|\\)/i.test(target)) {
      errors.push(`${label}: image must use a relative project path: ${raw}`);
      return;
    }
  } else {
    if (/^(?:[a-z][a-z\d+.-]*:|\/)/i.test(target)) return;
    if (!target.split('#')[0].endsWith('.md') && !target.startsWith('#')) return;
    links++;
  }
  const [filename, hash] = target.split('#');
  const resolved = filename ? path.resolve(path.dirname(file), filename) : file;
  const relative = path.relative(root, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    errors.push(`${label}: reference escapes the project: ${raw}`);
    return;
  }
  if (!await stat(resolved).then(info => info.isFile(), () => false)) {
    errors.push(`${label}: file does not exist: ${raw}`);
  } else if (kind === 'link' && hash && notes.has(resolved) && !notes.get(resolved).anchors.has(hash)) {
    errors.push(`${label}: heading does not exist: ${raw}`);
  }
}

async function inspect(file, tokens) {
  for (const token of tokens) {
    // Permalinks inserted by the renderer are website IDs, not source links.
    if (token.type === 'link_open' && token.attrGet('class') === 'header-anchor') continue;
    if (token.type === 'image') await check(file, 'image', token.attrGet('src'));
    if (token.type === 'link_open') await check(file, 'link', token.attrGet('href'));
    if (token.type === 'html_inline' || token.type === 'html_block') {
      for (const match of token.content.matchAll(/<img\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/gi)) await check(file, 'image', match[1]);
    }
    if (token.type === 'text' && /!\[\[[^\]]+\]\]/.test(token.content)) errors.push(`${path.relative(root, file)}: convert Obsidian image embeds to Markdown`);
    if (token.children && token.type !== 'image') await inspect(file, token.children);
  }
}
for (const [file, note] of notes) await inspect(file, note.tokens);
if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else {
  console.log(`Checked ${files.length} Markdown files, ${images} image references and ${links} chapter links: all portable references exist.`);
}
