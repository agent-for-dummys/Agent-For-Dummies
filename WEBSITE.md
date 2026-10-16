# 网站维护

网站用 VitePress 构建。中文首页来自根目录的 HOMEPAGE.md，英文首页来自 HOMEPAGE_EN.md；阅读页来自 docs/ 中的 Markdown。原始内容是唯一维护入口，不用再编辑生成后的网页文件。

## 本地查看

需要 Node.js 22 或更新版本。

```sh
npm install
npm run dev
```

打开 http://127.0.0.1:4173/ 。修改 HOMEPAGE.md、HOMEPAGE_EN.md 或 docs/ 后，网站内容自动更新。

当前项目目录：`D:\expe\agent-for-dummies`。

```sh
npm run build
npm run preview
```

构建结果位于 site/.vitepress/dist/ 。这是可以部署的静态网站。

## PyTorch 快速入门

页面入口为 `/pytorch`，包含 40 个函数学习项、80 道函数练习、30 道综合题及 30 道变式，配有真实用例、标准答案和解析。首次运行 `npm run setup` 安装环境，之后运行 `npm run learn` 同时启动网页和本机 CPU 判题服务，并自动打开浏览器。详细说明见 [oj/README.md](oj/README.md)。

官网保留函数学习、题目和题解，运行或提交时显示本地启动指南。读者下载或克隆仓库后，在自己电脑上练习，无需 GitHub 登录或云服务器。草稿、记录和布局保存在当前浏览器中，判题接口只接受本机请求。

## Agent 从 0 到 1

目录中可以切换 PyTorch 和 Agent。Agent 课程从《01-Agent基础与进阶》引入，前 16 节通过模型调用、提示模板、工具、ReAct、LangGraph 和 RAG 等短任务学习组件用法，后 12 节拆解 Pi 的关键函数并组装为可运行项目。教程包含代码示例和参数说明，任务页提供提示与可观察的完成结果，左右箭头用于切换任务，详见 [本地练习指南](oj/README.md)。

最终项目从关卡函数组装，支持本地资料检索、引用、记忆、SQLite 恢复、工具确认、LangGraph、规划与协作。练习不需要密钥，真实模型从本机 `.env` 读取读者自己填写的配置。运行方式与项目导出说明见 [本地练习指南](oj/README.md)。

持续编辑笔记时使用 `npm run dev` 自动同步。`npm run preview` 用于查看静态构建；每次重新构建后需要重启预览服务，让它读取新的资源清单。

## 内容与样式

- 修改文章：编辑 docs/ 中的原文件。
- 修改中文首页：编辑 HOMEPAGE.md；修改英文首页：编辑 HOMEPAGE_EN.md。
- 首页内容按 Markdown 原样生成，可在对应的首页文件中维护介绍、阅读入口和文档目录。
- 首页兼容 GitHub 粘贴图片时生成的 `<img>` 标签：同步时转换为自适应的 Markdown 图片；需要随项目分享的图片应先保存到 assets/ 并改为相对路径。代码块中的图片示例保持为代码。
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

网站基础路径根据当前仓库名自动生成，因此 Fork 后可以在自己的 Pages 地址构建。如果使用自定义域名，将工作流中的 SITE_BASE 改为 / 。

文档、Transformer 下级目录与 NLP 阅读入口统一从源文件同步。修改后先在本地审阅，确认结果后提交并推送，以触发官网更新。

## 图片与补充笔记

- 图片可用 `![说明|420](相对路径)` 指定显示宽度，单位为像素；官网会去掉说明中的宽度标记，保持比例，并在窄屏上自动缩小。未指定宽度的图片沿用默认样式。解析规则在 scripts/image-widths.mjs 中。
- Markdown 图片使用相对于原文件的路径；分享时将 docs/ 与 assets/ 一起复制。不要使用电脑绝对路径、`/assets/` 根路径或 Obsidian 的 `![[图片]]` 嵌入语法。
- NLP 配图位于 assets/nlp/source/，Hessian 示意图位于 assets/nlp/hessian/。
- Transformer 的两篇补充笔记使用 assets/transformer/self-attention/ 与 assets/transformer/architecture/。
- 根目录 README 的内容预览图保存在 assets/previews/，不再依赖 GitHub 附件。
- 补充笔记的父章节、源文件与网站路由统一维护在 scripts/catalog.mjs 的 supplements 中，自动用于侧栏与完整目录。
- 构建仅从项目内读取 Markdown 与 assets/；不再从 Typora 缓存或其他电脑路径临时复制图片。
- 章节链接在源 Markdown 中使用标准标题锚点；同步脚本根据实际标题转换成 VitePress 的锚点，兼容编号与中文标点。
- 运行 `npm run check:content` 检查源 Markdown 的图片路径、文件存在性及章节链接；构建前自动执行。

## 算法交互图解

Self-Attention 与 Transformer 补充笔记包含可翻页的 SVG 图解，支持切换 Query、上一步 / 下一步、播放 / 暂停、播放速度与重播本步。离开可见区域或切换页面时自动暂停；系统开启“减少动效”时关闭图内动画。

Self-Attention 默认显示矩阵视图，也可以切换到关系图。矩阵按“结果 = 运算矩阵 × 输入”排列，各图解统一使用蓝、青绿和灰色，配色变量维护在 AlgorithmWalkthrough.vue 中。乘法依次高亮参与计算的行、列与元素，显示累加并填入结果格子；投影步骤可切换 Q / K / V。沿用正文的列向量约定：`S = KᵀQ` 的行对应 Key、列对应 Query，Softmax 按列归一化，最终用 `B = VA` 汇总。

图解只保留一步一句说明，整块高度控制在 400px 内；左右翻页按钮固定在图形两侧，小屏幕在图内横向滑动。Sequence Mask 图固定并排显示 b¹ / b² / b³，与下方三个输入一一对齐；翻页只切换当前输出的连接和未来位置的遮挡状态，不播放数据流动动画。可点击输入或输出切词，也可自动翻页。Padding Mask 图分别展示不同句长、PAD 补齐、PAD 屏蔽，填入和遮挡使用短动画。两种图解分别插入原文的 3.3.1 Padding Mask 与 3.3.2 Sequence Mask 小节。图内不产生鼠标星光和点击涟漪。

在源 Markdown 中用下面两行插入图解：

```markdown
::: algorithm attention
:::
```

可用类型是 `attention`（注意力数值计算）、`multi-head`（多头拼接与投影）、`transformer`（Encoder–Decoder 流程）、`mask`（因果掩码的逐词连接）和 `padding`（PAD 补齐与屏蔽）。网站解析规则位于 scripts/algorithm-walkthroughs.mjs；组件和计算位于 site/.vitepress/theme/algorithms/。

数值图解使用手工设定的二维向量和投影矩阵，权重与输出实时计算；模型结构及翻译词序列是教学示意，不调用真实模型。图解仅在网站上交互显示，普通 Markdown 阅读器仍可阅读原有文字、公式与配图。
