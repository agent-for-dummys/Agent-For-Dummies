import { readdir, readFile, mkdir, writeFile, cp } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { chapters } from './catalog.mjs';

export const root = fileURLToPath(new URL('../', import.meta.url));
const site = path.join(root, 'site');
const repository = 'https://github.com/MorningRainn/Agent-For-Dummies';

async function writeChanged(file, content) {
  await mkdir(path.dirname(file), { recursive: true });
  let previous;
  try { previous = await readFile(file, 'utf8'); } catch {}
  if (previous !== content) await writeFile(file, content);
}

function rewriteLinks(source, files) {
  return source.replace(/\]\(([^)]+)\)/g, (match, destination) => {
    let target;
    try { target = decodeURIComponent(destination); } catch { return match; }
    if (/(?:\.\.\/)*assets\//.test(target)) return `](/assets/${target.split('/').pop()})`;
    if (target === 'README.md') return '](/)';
    if (target === 'README_EN.md') return '](/en)';
    if (target === 'LICENSE') return `](${repository}/blob/main/LICENSE)`;
    const [file, hash] = target.split('#');
    const index = files.indexOf(path.basename(file));
    if (index >= 0) return `](${chapters[index].link}${hash ? '#' + hash : ''})`;
    return match;
  });
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

export async function syncContent() {
  const files = (await readdir(path.join(root, 'docs'))).filter(file => /^\d{2}.*\.md$/.test(file)).sort();
  if (files.length !== chapters.length || files.some((file, i) => Number(file.slice(0, 2)) !== chapters[i].id)) {
    throw new Error('Update scripts/catalog.mjs when adding or renumbering chapters.');
  }
  for (const [i, chapter] of chapters.entries()) {
    const original = (await readFile(path.join(root, 'docs', files[i]), 'utf8')).replace(/\r\n/g, '\n');
    const body = normalizeHeadings(rewriteLinks(original, files)).replace(/^\s*[-*_]{3,}\s*\n/, '').trim();
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
  for (const [input, output, title, pageClass] of [['README.md', 'index.md', '首页', 'readme-page'], ['README_EN.md', 'en.md', 'English', 'readme-page']]) {
    const source = rewriteLinks((await readFile(path.join(root, input), 'utf8')).replace(/\r\n/g, '\n'), files).replace(/^# 🤖 /, '# ');
    const body = presentReadme(source, input === 'README_EN.md' ? 'en' : 'zh');
    await writeChanged(path.join(site, output), `---\ntitle: ${title}\nsidebar: false\nsearch: false\npageClass: ${pageClass}\nsource: ${input}\nprev: false\nnext: false\n---\n\n${body}`);
  }
  const catalog = `---\ntitle: 文档目录\nsidebar: false\nsearch: false\noutline: false\npageClass: catalog-page\nprev: false\nnext: false\n---\n\n# 文档目录\n\n` + (await import('./catalog.mjs')).groups.map(group => `## ${group.title}\n\n${chapters.filter(chapter => group.ids.includes(chapter.id)).map(chapter => `- [${String(chapter.id).padStart(2, '0')}　${chapter.title}](${chapter.link})`).join('\n')}`).join('\n\n');
  await writeChanged(path.join(site, 'catalog.md'), catalog);
  await mkdir(path.join(site, 'public'), { recursive: true });
  await cp(path.join(root, 'assets'), path.join(site, 'public', 'assets'), { recursive: true });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await syncContent();
  console.log(`Synced README and ${chapters.length} chapters.`);
}
