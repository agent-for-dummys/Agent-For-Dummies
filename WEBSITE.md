# 网站维护

网站用 VitePress 构建。首页来自根目录的 README.md；阅读页来自 docs/ 中的 Markdown。原始内容是唯一维护入口，不用再编辑一份网页内容。

## 本地查看

需要 Node.js 22 或更新版本。

```sh
npm install
npm run dev
```

打开 http://127.0.0.1:4173/ 。修改 README.md 或 docs/ 后，阅读页自动更新。

当前项目目录：`D:\expe\agent-for-dummies`。

```sh
npm run build
npm run preview
```

构建结果位于 site/.vitepress/dist/ 。这是可以部署的静态网站。

## 内容与样式

- 修改文章：编辑 docs/ 中的原文件。
- 修改首页：编辑 README.md。
- 首页展示 README 的标题、简介、阅读入口、目录与许可信息；生成时精简重复的引导段落。可在 scripts/sync-content.mjs 的 presentReadme 中调整。
- 增加文章或调整分类：在 scripts/catalog.mjs 中补充编号、标题、分类和英文路由。
- 修改排版与配色：编辑 site/.vitepress/theme/style.css。
- 网站启动和构建时自动生成页面、修正文档图片路径和整理标题层级；原文件保持不变。
- 站内全文搜索覆盖标题和正文，支持中文词语、英文术语与代码内容。浏览器端检索，不依赖外部搜索服务。
- 搜索只索引学习文章，排除首页、英文首页和目录。同一篇文章的段落合并为一个结果，优先显示直接命中标题或正文的段落，摘要最多 120 字；点击结果定位到最相关的段落。
- 搜索组件：site/.vitepress/theme/DocumentSearch.vue；结果合并与排序：search-ranking.ts。
- 网站标识使用 site/public/logo.png，原图来自 D:\expe\logo.png。更新标识时替换项目内的 logo.png 即可。
- 字体优先加载 Google Fonts 的 DM Sans、Noto Sans SC 与 JetBrains Mono；不可用时使用本机字体，内容和搜索仍可正常使用。
- 鼠标移动会产生短暂星光，悬停链接与按钮时轻微闪烁；粒子数量受限，停止移动后自动清理。系统开启“减少动效”时停用。

## GitHub Pages

仓库中已加入 .github/workflows/pages.yml。将改动推送到 main 后，在仓库 Settings → Pages → Source 中选择 GitHub Actions。工作流会构建并发布。

默认仓库地址的基础路径为 /Agent-For-Dummies/ 。如果使用自定义域名，将工作流中的 SITE_BASE 改为 / 。

此版本只新增网站源码与发布配置，没有修改原始笔记，也没有向 GitHub 推送或发布。
