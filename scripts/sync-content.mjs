import { readdir, readFile, mkdir, writeFile, cp } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createMarkdownRenderer } from 'vitepress';
import { chapters, supplements } from './catalog.mjs';

export const root = fileURLToPath(new URL('../', import.meta.url));
const site = path.join(root, 'site');
const repository = 'https://github.com/agent-for-dummys/Agent-For-Dummies';

async function writeChanged(file, content) {
  await mkdir(path.dirname(file), { recursive: true });
  let previous;
  try { previous = await readFile(file, 'utf8'); } catch {}
  if (previous !== content) await writeFile(file, content);
}

function rewriteLinks(source, files, sourceFile, anchors) {
  return source.replace(/\]\(([^)]+)\)/g, (match, destination) => {
    if (/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(destination.trim())) return match;
    let target;
    try { target = decodeURIComponent(destination); } catch { return match; }
    const [file, hash] = target.split('#');
    const resolved = file ? path.resolve(path.dirname(path.join(root, sourceFile)), file) : path.join(root, sourceFile);
    const relative = path.relative(root, resolved).split(path.sep).join('/');
    const destinationHash = anchors.get(relative)?.get(hash) || hash;
    const suffix = hash ? '#' + destinationHash : '';
    if (!file) return `](${suffix})`;
    if (relative.startsWith('assets/')) return `](/${encodeURI(relative)}${suffix})`;
    if (relative === 'README.md') return '](/)';
    if (relative === 'README_EN.md') return '](/en)';
    if (relative === 'LICENSE') return `](${repository}/blob/main/LICENSE)`;
    const supplement = supplements.find(note => note.source === relative);
    if (supplement) return `](${supplement.link}${suffix})`;
    const index = files.findIndex(name => relative === `docs/${name}`);
    if (index >= 0) return `](${chapters[index].link}${suffix})`;
    return match;
  });
}

function prepareReadme(source) {
  const convert = fragment => fragment.replace(/<img\b[^>]*>/gi, tag => {
    const src = tag.match(/\ssrc\s*=\s*(["'])(.*?)\1/is)?.[2];
    if (!src || (/^[a-z][a-z\d+.-]*:/i.test(src) && !/^https?:\/\//i.test(src))) return tag;
    const alt = tag.match(/\salt\s*=\s*(["'])(.*?)\1/is)?.[2];
    const label = (!alt || alt === 'image' ? 'Website image' : alt).replace(/[\\\[\]]/g, '\\$&').replace(/\r?\n/g, ' ');
    const url = src.replace(/&amp;/g, '&').replace(/ /g, '%20').replace(/\(/g, '%28').replace(/\)/g, '%29');
    return `\n\n![${label}](${url})\n\n`;
  });
  const output = [];
  const plain = [];
  let fence = null;
  const flush = () => {
    if (plain.length) output.push(convert(plain.join('\n')));
    plain.length = 0;
  };
  for (const line of source.split('\n')) {
    const marker = line.match(/^[ \t]*(`{3,}|~{3,})/);
    if (fence) {
      output.push(line);
      if (marker && marker[1][0] === fence[0] && marker[1].length >= fence.length && !line.slice(marker[0].length).trim()) fence = null;
    } else if (marker) {
      flush(); output.push(line); fence = marker[1];
    } else plain.push(line);
  }
  flush();
  return output.join('\n');
}

// Normalize heading depth for a readable outline without changing source notes.
function normalizeHeadings(source) {
  const stack = [];
  let fence = null;
  return source.split('\n').map(line => {
    const marker = line.match(/^\s*(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence = marker[1][0];
      else if (marker[1][0] === fence) fence = null;
      return line;
    }
    if (fence) return line;
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (!heading) return line;
    const level = heading[1].length;
    while (stack.length && stack.at(-1) >= level) stack.pop();
    stack.push(level);
    return '#'.repeat(Math.min(stack.length + 1, 6)) + ' ' + heading[2];
  }).join('\n');
}

// Present README's useful content without repeated onboarding paragraphs.
function presentReadme(source, language) {
  const english = language === 'en';
  const parts = source.split(/^##\s+(.+)$/m);
  const introduction = parts[0].trim().split(/\n\s*\n/).filter(block => /^(#\s|>\s|\[)/.test(block.trim())).join('\n\n');
  const sections = [];
  for (let i = 1; i < parts.length; i += 2) {
    const heading = parts[i].trim();
    const body = parts[i + 1]?.trim() || '';
    if (heading === '使用方式' || heading === 'How to Use These Notes') continue;
    if (heading === '从这里开始' || heading === 'Start Here') {
      const labels = english ? ['01 Agents', '02 Tool Calling', '03 RAG'] : ['01 Agent', '02 工具调用', '03 RAG'];
      sections.push(`## ${heading}\n\n${chapters.slice(0, 3).map((chapter, index) => `[${labels[index]}](${chapter.link})`).join('　→　')}`);
    } else if (heading === '说明' || heading === 'Notes') {
      const license = body.split(/\n\s*\n/).filter(block => block.includes('[CC BY 4.0]')).map(block => block
        .replace('`assets/` 中的部分图片可能属于原作者，公开复用前请确认其授权。', '')
        .replace('Some images in `assets/` may belong to their original creators; please confirm their licenses before public reuse.', '')
        .trim());
      if (license.length) sections.push(license.join('\n\n'));
    } else {
      sections.push(`## ${heading}\n\n${body}`);
    }
  }
  return [introduction, ...sections].join('\n\n') + '\n';
}

// GitHub and VitePress assign different IDs to numbered/punctuated headings.
// Resolve each source anchor against the website renderer before rewriting links.
export function markdownHeadingSlug(title) {
  return title.trim().toLowerCase().replace(/[^\p{L}\p{M}\p{N}\s_-]/gu, '').replace(/ /g, '-');
}

export async function syncContent() {
  const files = (await readdir(path.join(root, 'docs'))).filter(file => /^\d{2}.*\.md$/.test(file)).sort();
  if (files.length !== chapters.length || files.some((file, i) => Number(file.slice(0, 2)) !== chapters[i].id)) {
    throw new Error('Update scripts/catalog.mjs when adding or renumbering chapters.');
  }
  const renderer = await createMarkdownRenderer(site);
  const anchors = new Map();
  for (const source of [...files.map(file => `docs/${file}`), ...supplements.map(note => note.source)]) {
    const tokens = renderer.parse(await readFile(path.join(root, source), 'utf8'), {});
    const slugs = new Map();
    const counts = new Map();
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type !== 'heading_open') continue;
      const title = tokens[i + 1].children.filter(token => token.type === 'text' || token.type === 'code_inline').map(token => token.content).join('');
      const slug = markdownHeadingSlug(title);
      const count = counts.get(slug) || 0;
      counts.set(slug, count + 1);
      slugs.set(count ? `${slug}-${count}` : slug, tokens[i].attrGet('id'));
    }
    anchors.set(source, slugs);
  }
  for (const [i, chapter] of chapters.entries()) {
    const original = (await readFile(path.join(root, 'docs', files[i]), 'utf8')).replace(/\r\n/g, '\n');
    const body = normalizeHeadings(rewriteLinks(original.replace(/^# .+\n+/, ''), files, `docs/${files[i]}`, anchors)).replace(/^\s*[-*_]{3,}\s*\n/, '').trim();
    const meta = {
      title: chapter.title,
      description: `${chapter.group} · ${chapter.title}学习笔记`,
      chapter: String(chapter.id).padStart(2, '0'),
      category: chapter.group,
      source: `docs/${files[i]}`,
      prev: i ? { text: chapters[i - 1].title, link: chapters[i - 1].link } : { text: '首页', link: '/' },
      next: i < chapters.length - 1 ? { text: chapters[i + 1].title, link: chapters[i + 1].link } : false
    };
    await writeChanged(path.join(site, 'notes', `${chapter.slug}.md`), `---\n${Object.entries(meta).map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join('\n')}\n---\n\n# ${chapter.title}\n\n${body}\n`);
  }
  for (const note of supplements) {
    const original = (await readFile(path.join(root, note.source), 'utf8')).replace(/\r\n/g, '\n');
    const body = normalizeHeadings(rewriteLinks(original.replace(/^# .+\n+/, ''), files, note.source, anchors)).trim();
    const meta = {
      title: note.title,
      description: `模型基础 · ${note.title}`,
      category: '模型基础',
      source: note.source,
      prev: { text: 'Transformer 基础', link: '/notes/transformer' },
      next: false
    };
    await writeChanged(path.join(site, `${note.link.slice(1)}.md`), `---\n${Object.entries(meta).map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join('\n')}\n---\n\n# ${note.title}\n\n${body}\n`);
  }
  const homepage = (await readFile(path.join(root, 'HOMEPAGE.md'), 'utf8')).replace(/\r\n/g, '\n');
  const homepageBody = rewriteLinks(prepareReadme(homepage), files, 'HOMEPAGE.md', anchors);
  await writeChanged(
    path.join(site, 'index.md'),
    `---\ntitle: 首页\nsidebar: false\nsearch: false\npageClass: readme-page\nsource: HOMEPAGE.md\nprev: false\nnext: false\n---\n\n${homepageBody.trim()}\n`
  );
  const englishHomepage = (await readFile(path.join(root, 'HOMEPAGE_EN.md'), 'utf8')).replace(/\r\n/g, '\n');
  const englishHomepageBody = rewriteLinks(prepareReadme(englishHomepage), files, 'HOMEPAGE_EN.md', anchors);
  await writeChanged(
    path.join(site, 'en.md'),
    `---\ntitle: English\nsidebar: false\nsearch: false\npageClass: readme-page\nsource: HOMEPAGE_EN.md\nprev: false\nnext: false\n---\n\n${englishHomepageBody.trim()}\n`
  );
  const catalog = `---\ntitle: 文档目录\nsidebar: false\nsearch: false\noutline: false\npageClass: catalog-page\nprev: false\nnext: false\n---\n\n# 文档目录\n\n` + (await import('./catalog.mjs')).groups.map(group => `## ${group.title}\n\n${chapters.filter(chapter => group.ids.includes(chapter.id)).map(chapter => [`- [${String(chapter.id).padStart(2, '0')}　${chapter.title}](${chapter.link})`, ...chapter.children.map(note => `  - [${note.title}](${note.link})`)].join('\n')).join('\n')}`).join('\n\n');
  await writeChanged(path.join(site, 'catalog.md'), catalog);
  await mkdir(path.join(site, 'public'), { recursive: true });
  await cp(path.join(root, 'assets'), path.join(site, 'public', 'assets'), { recursive: true });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await syncContent();
  console.log(`Synced HOMEPAGE.md, HOMEPAGE_EN.md and ${chapters.length} chapters.`);
}
