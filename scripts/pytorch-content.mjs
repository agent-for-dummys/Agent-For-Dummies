import fs from 'node:fs';
import path from 'node:path';
import MarkdownIt from 'markdown-it';
import mathjax from 'markdown-it-mathjax3';

// Course prose is rendered during the build, using the same math renderer as the notes.
export function pytorchContent(root) {
  const id = '\0virtual:pytorch-content';
  const agentId = '\0virtual:agent-content';
  const source = path.join(root, 'oj/course.json');
  const agentSource = path.join(root, 'oj/agent_course.json');
  const md = new MarkdownIt({ html: false, linkify: false }).use(mathjax);
  const agentMd = new MarkdownIt({ html: false, linkify: false }).use(mathjax);
  const renderFence = agentMd.renderer.rules.fence;
  agentMd.renderer.rules.fence = (...args) => '<div class="agent-code"><button type="button" class="copy-code" aria-label="复制代码"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="6" width="9" height="11" rx="1.5"/><path d="M12 6V3H3v11h4"/></svg><span>复制</span></button>' + renderFence(...args) + '</div>';
  return {
    name: 'pytorch-course-content',
    resolveId(name) { if (name === 'virtual:pytorch-content') return id; if(name==='virtual:agent-content')return agentId; },
    load(name) {
      if(name===agentId){
        this.addWatchFile(agentSource);
        const agent=JSON.parse(fs.readFileSync(agentSource,'utf8'));
        const content=Object.fromEntries(agent.chapters.map(ch=>[ch.id,{
          lesson:agentMd.render(ch.lesson), task:md.render(ch.task),
          hints:ch.hints.map(item=>md.renderInline(item)), success:md.render(ch.success),
          interface:{
            parameters:ch.interface.parameters.map(p=>md.renderInline(p.description)),
            returns:md.renderInline(ch.interface.returns),
            requirements:ch.interface.requirements.map(text=>md.renderInline(text)),
            explanation:md.renderInline(ch.interface.example.explanation)
          }
        }]));
        return `export default ${JSON.stringify(content)}`;
      }
      if (name !== id) return;
      this.addWatchFile(source);
      this.addWatchFile(agentSource);
      const course = JSON.parse(fs.readFileSync(source, 'utf8'));
      const lessons = Object.fromEntries(course.modules.flatMap(module => module.lessons.map((lesson, i) => [`${module.id}:${i}`, md.render(lesson.detail || lesson.description)])));
      const problems = Object.fromEntries(course.problems.map(problem => [problem.id, {
        statement: md.render(problem.statement),
        formula: md.render(problem.formula || ''),
        analysis: problem.analysis.map(text => md.render(text)),
        parameters: problem.parameters.map(p => md.renderInline(p.description.replace(/。$/, '')+(['int','float'].includes(p.type)&&!p.description.includes(p.type)?`，类型为 \`${p.type}\``:'')+'。')),
        returns: md.renderInline(problem.returns.replace(/^返回/, '')),
        explanations: problem.examples.map(e => md.renderInline(e.explanation || '')),
        limits: [...problem.ranges, ...problem.constraints].map(text => md.renderInline(text))
      }]));
      return `export default ${JSON.stringify({ lessons, problems })}`;
    },
    handleHotUpdate(ctx) {
      if (![source,agentSource].includes(path.resolve(ctx.file))) return;
      const module = ctx.server.moduleGraph.getModuleById(id);
      const agentModule=ctx.server.moduleGraph.getModuleById(agentId);
      for(const m of [module,agentModule])if(m)ctx.server.moduleGraph.invalidateModule(m);
      return [...ctx.modules,...[module,agentModule].filter(Boolean)];
    }
  };
}
