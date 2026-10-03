import { chapters } from '../../../scripts/catalog.mjs';

export interface SectionHit {
  id: string;
  title: string;
  titles: string[];
  text?: string;
  score: number;
}

export interface ArticleResult {
  page: string;
  href: string;
  title: string;
  category: string;
  section: string;
  snippet: string;
  score: number;
}

const compact = (value: string) => value.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}_]/gu, '');

export function queryTerms(query: string): string[] {
  return [...new Set(query.normalize('NFKC').match(/[\p{Script=Han}]+|[\p{Script=Latin}\p{N}_]+/gu) || [])];
}

function matchingParts(query: string): string[] {
  const terms = [];
  for (const token of new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment(query.toLowerCase())) {
    if (token.isWordLike && (token.segment.length > 1 || /[a-z\d]/i.test(token.segment))) terms.push(compact(token.segment));
  }
  return [...new Set(terms)];
}

function sectionScore(hit: SectionHit, query: string, parts: string[]): number {
  const title = compact(hit.title || '');
  const body = compact(hit.text || '');
  const exact = compact(query);
  let score = hit.score;
  if (title === exact) score += 600;
  else if (title.includes(exact)) score += 400;
  if (body.includes(exact)) score += 75;
  for (const part of parts) {
    if (title.includes(part)) score += 32;
    if (body.includes(part)) score += 8;
  }
  return score;
}

function excerpt(text: string, query: string): string {
  const clean = text.replace(/\s+/g, ' ').trim();
  const terms = queryTerms(query).map(term => term.toLowerCase());
  const lower = clean.toLowerCase();
  const positions = terms.map(term => lower.indexOf(term)).filter(position => position >= 0);
  const start = positions.length ? Math.max(0, Math.min(...positions) - 30) : 0;
  return (start ? '…' : '') + clean.slice(start, start + 120) + (clean.length > start + 120 ? '…' : '');
}

export function rankArticles(hits: SectionHit[], query: string): ArticleResult[] {
  if (!query.trim()) return [];
  const parts = matchingParts(query);
  const grouped = new Map<string, SectionHit[]>();
  for (const hit of hits) {
    const page = String(hit.id).split('#')[0];
    if (!chapters.some(chapter => page.replace(/\.html$/, '').endsWith(chapter.link))) continue;
    const sections = grouped.get(page) || [];
    if (!sections.some(section => section.id === hit.id)) sections.push(hit);
    grouped.set(page, sections);
  }
  const ranked = [...grouped.entries()].map(([page, sections]) => {
    const chapter = chapters.find(chapter => page.replace(/\.html$/, '').endsWith(chapter.link))!;
    sections.sort((a, b) => sectionScore(b, query, parts) - sectionScore(a, query, parts));
    const best = sections[0];
    const preview = best.text?.trim() ? best : sections.find(hit => hit.text?.trim()) || best;
    const titleMatch = compact(chapter.title).includes(compact(query));
    return {
      page,
      href: titleMatch ? page : best.id,
      title: chapter.title,
      category: chapter.group,
      section: compact(preview.title || '') === compact(chapter.title) ? '' : preview.title || '',
      snippet: excerpt(preview.text || '', query),
      score: sectionScore(best, query, parts) + (titleMatch ? 250 : 0)
    };
  }).sort((a, b) => b.score - a.score).slice(0, 12);
  // A mixed-language title query such as "agent基础" clearly names a note;
  // avoid incidental User-Agent + "基础" matches from unrelated articles.
  if (/[a-z]/i.test(query) && /[\p{Script=Han}]/u.test(query)) {
    const titleMatches = ranked.filter(result => compact(result.title).includes(compact(query)));
    if (titleMatches.length) return titleMatches;
  }
  return ranked;
}

export function highlight(text: string, query: string): { text: string; matched: boolean }[] {
  const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const patterns = queryTerms(query).sort((a, b) => b.length - a.length).map(term => /^[\p{Script=Han}]+$/u.test(term) ? [...term].map(escape).join('\\s*') : escape(term));
  if (!patterns.length) return [{ text, matched: false }];
  const expression = new RegExp(patterns.join('|'), 'gi');
  const output = [];
  let last = 0;
  for (const match of text.matchAll(expression)) {
    if (match.index! > last) output.push({ text: text.slice(last, match.index), matched: false });
    output.push({ text: match[0], matched: true });
    last = match.index! + match[0].length;
  }
  if (last < text.length) output.push({ text: text.slice(last), matched: false });
  return output;
}
