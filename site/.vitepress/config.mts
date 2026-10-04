import { defineConfig } from 'vitepress';
import { chapters, groups } from '../../scripts/catalog.mjs';
import { syncContent, root } from '../../scripts/sync-content.mjs';
import path from 'node:path';

const base = process.env.SITE_BASE || '/';

export default defineConfig({
  lang: 'zh-CN',
  title: 'Agent For Dummies',
  description: 'Agent、RAG、大模型与计算机基础的开源学习笔记。',
  base,
  cleanUrls: true,
  appearance: true,
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: `${base}logo.png` }],
    ['meta', { name: 'theme-color', content: '#ffffff' }]
  ],
  markdown: {
    math: true,
    image: { lazyLoading: true },
    config(md) { md.set({ html: false }); }
  },
  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'Agent For Dummies',
    nav: [
      { text: '首页', link: '/' },
      { text: '文档目录', link: '/catalog' }
    ],
    sidebar: groups.map(group => ({
      text: group.title,
      items: chapters.filter(chapter => group.ids.includes(chapter.id)).map(chapter => ({
        text: `${String(chapter.id).padStart(2, '0')}　${chapter.title}`,
        link: chapter.link
      }))
    })),
    outline: { level: [2, 3], label: '本页目录' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/MorningRainn/Agent-For-Dummies' }],
    editLink: {
      pattern: ({ frontmatter }) => frontmatter.source ? `https://github.com/MorningRainn/Agent-For-Dummies/edit/main/${encodeURI(frontmatter.source)}` : '',
      text: '在 GitHub 编辑此页'
    },
    docFooter: { prev: '上一篇', next: '下一篇' },
    sidebarMenuLabel: '章节',
    outlineTitle: '本页目录',
    returnToTopLabel: '回到顶部',
    darkModeSwitchLabel: '切换日间与夜间主题',
    lightModeSwitchTitle: '切换到日间',
    darkModeSwitchTitle: '切换到夜间',
    notFound: { title: '页面未找到', quote: '可以从目录继续阅读。', linkLabel: '返回首页', linkText: '返回首页' },
    search: {
      provider: 'local',
      options: {
        detailedView: false,
        disableDetailedView: true,
        translations: {
          button: { buttonText: '搜索笔记', buttonAriaLabel: '全文搜索笔记' },
          modal: {
            displayDetails: '显示正文预览',
            resetButtonTitle: '清空搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '没有找到相关内容',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' }
          }
        },
        miniSearch: {
          options: {
            storeFields: ['title', 'titles', 'text'],
            tokenize(text) {
              const normalized = text.normalize('NFKC').toLowerCase();
              const terms = new Set<string>();
              for (const item of new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment(normalized)) {
                if (item.isWordLike) terms.add(item.segment);
              }
              for (const run of normalized.match(/[\p{Script=Han}]+/gu) || []) {
                const chars = [...run];
                for (let size = 2; size <= 3; size++) {
                  for (let start = 0; start + size <= chars.length; start++) terms.add(chars.slice(start, start + size).join(''));
                }
              }
              return [...terms];
            }
          },
          searchOptions: { combineWith: 'AND', prefix: true, fuzzy: false, boost: { title: 5, titles: 2, text: 1 } }
        }
      }
    }
  },
  vite: {
    plugins: [{
      name: 'sync-repository-notes',
      configureServer(server) {
        const sources = ['HOMEPAGE.md', 'HOMEPAGE_EN.md', 'docs', 'assets'].map(file => path.join(root, file));
        server.watcher.add(sources);
        let pending = Promise.resolve();
        server.watcher.on('all', (event, file) => {
          if (['change', 'add', 'unlink'].includes(event) && sources.some(source => file === source || file.startsWith(source + path.sep))) {
            pending = pending.then(() => syncContent()).catch(error => server.config.logger.error(String(error)));
          }
        });
      }
    }]
  }
});
