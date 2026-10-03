export const groups = [
  { title: 'Agent 应用', key: 'agent', ids: [1, 2, 3] },
  { title: '模型基础', key: 'models', ids: [4, 5, 6, 7, 8] },
  { title: '工程基础', key: 'engineering', ids: [9, 10, 11] },
  { title: '多模态', key: 'multimodal', ids: [12] }
];

export const chapters = [
  { id: 1, slug: 'agent', title: 'Agent 基础与进阶' },
  { id: 2, slug: 'tools', title: 'Function Calling、MCP、Skills' },
  { id: 3, slug: 'rag', title: 'RAG' },
  { id: 4, slug: 'transformer', title: 'Transformer 基础' },
  { id: 5, slug: 'fine-tuning', title: '模型微调' },
  { id: 6, slug: 'ai-concepts', title: '常用 AI 概念' },
  { id: 7, slug: 'models', title: '常见大模型' },
  { id: 8, slug: 'machine-learning', title: '机器学习' },
  { id: 9, slug: 'elasticsearch', title: 'Elasticsearch' },
  { id: 10, slug: 'full-stack', title: '全栈基础' },
  { id: 11, slug: 'systems-and-networks', title: '操作系统、计算机网络' },
  { id: 12, slug: 'vlm-evaluation', title: 'VLM 评测' }
].map(chapter => ({ ...chapter, group: groups.find(group => group.ids.includes(chapter.id)).title, link: `/notes/${chapter.slug}` }));
