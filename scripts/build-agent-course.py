"""Build a beginner-first course, then focused tasks in the Pi project."""
import ast
import json
import re
import sys
from pathlib import Path

import black

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_project.learning import LESSONS
from agent_project.pi_lessons import PI_LESSONS
from agent_project.task_specs import SPECS
from agent_project.component_guides import NOTES, enrich
from agent_project.panel_examples import PREVIEWS,LIVE_INPUT,RUNTIME_OUTPUT

MODE = black.Mode(line_length=68, magic_trailing_comma=True)
ENV = "MODEL_PROVIDER=openai\nMODEL_API_KEY=\nMODEL_NAME=\nMODEL_BASE_URL=\nWEATHER_API_KEY=\nWEATHER_API_URL=https://eolink.o.apispace.com/456456/weather/v001/now\n"


def formatted(code):
    return black.format_str(code.strip() + "\n", mode=MODE)


def focused_starter(code, focus):
    lines = code.splitlines()
    tree = ast.parse(code)
    if focus == "assembly":
        start = next(i for i, line in enumerate(lines) if 'return MiniPi(' in line)
        lines[start:] = ['    # TODO: 把这些组件传给 MiniPi，返回组装好的 Agent。',
                         '    raise NotImplementedError']
    elif focus == "edges":
        start = next(i for i, line in enumerate(lines) if 'graph.add_edge(START' in line)
        lines[start:] = ['    # TODO: 连接模型、工具与结束节点，再编译图。',
                         '    raise NotImplementedError']
    else:
        names = focus.split('.')
        parent = tree
        for name in names:
            parent = next(node for node in parent.body if getattr(node, 'name', None) == name)
        first = parent.body[0].lineno - 1
        indent = ' ' * parent.body[0].col_offset
        lines[first:parent.end_lineno] = [indent + '# TODO: 根据本节示例完成这一步。',
                                        indent + 'raise NotImplementedError']
    return formatted('\n'.join(lines))


def audit_components(chapter):
    """Every imported component must be explained and used in learning examples."""
    examples = re.findall(r'```python\n(.*?)```', chapter['lesson'], re.S)
    prose = re.sub(r'```.*?```', '', chapter['lesson'], flags=re.S)
    imported = {}
    for source in [chapter['example'], chapter['starter'], *examples]:
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported[(node.module or '') + '.' + alias.name] = alias.asname or alias.name
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported[alias.name] = alias.asname or alias.name.split('.')[0]
    used = {node.id for source in examples for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    for qualified, name in imported.items():
        if not re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', prose):
            raise ValueError(f"{chapter['id']}: 学习正文缺少导入组件说明 {qualified}")
        if name not in used:
            raise ValueError(f"{chapter['id']}: 学习代码缺少导入组件用法 {qualified}")
    return sorted(imported)


def build():
    files = {'.env': ENV, 'practice/__init__.py': '', 'mini_pi/__init__.py': '',
             'workspace/hello.py': 'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("reader"))\n',
             'workspace/README.md': '# 示例项目\nhello.py 中有一个问候函数。\n',
             'workspace/AGENTS.md': '# 项目说明\n先阅读，再修改，最后检查结果。\n',
             'workspace/skills/review/SKILL.md': '# 代码审查\n先阅读代码，再检查边界输入。\n',
             'workspace/prompts/review.md': '请审查：{question}\n',
             '.gitignore': '.env\n.mini-pi/\n__pycache__/\n',
             'requirements.txt': 'langchain[mcp]==1.4.6\nlangchain-openai==1.7.2\nfastmcp==4.1.0\nlanggraph==1.2.15\nlanggraph-checkpoint-sqlite==3.1.2\npython-dotenv==1.2.4\nhttpx==0.28.1\n',
             'README.md': '# 我的 mini-pi\n\n先安装 `pip install -r requirements.txt`，再填写 `.env`。\n\n运行 `python -m mini_pi.cli --demo` 验证离线流程。\n\n真实运行：`python -m mini_pi.cli "解释 hello.py"`。\n'}
    files['practice/weather_support.py'] = formatted((ROOT/'agent_project/weather_support.py').read_text(encoding='utf-8'))
    files['practice/weather_cities.csv'] = (ROOT/'agent_project/data/weather_cities.csv').read_text(encoding='utf-8')
    reference = {}
    excluded = {'__init__', 'curriculum', 'course_extensions', 'teaching', 'learning', 'pi_lessons', 'task_specs', 'component_guides', 'weather_support', 'panel_examples'}
    for source in (ROOT/'agent_project').glob('*.py'):
        if source.stem not in excluded:
            reference['mini_pi/' + source.name] = formatted(source.read_text(encoding='utf-8'))
    files.update(reference)
    chapters = []
    foundation=[item for item in LESSONS if item['id']!='mcp_tools']
    foundation.extend(item for item in LESSONS if item['id']=='mcp_tools')
    for original in foundation:
        chapter = dict(original)
        if chapter['id'] in {'conversation','workflow','checkpoint','async_reply'}:
            chapter.update(live=True,mode='model')
        if chapter['id'] in {'conversation','checkpoint'}:
            chapter['question']='我叫什么？'
        chapter['example'] = formatted(chapter['example'])
        chapter['starter'] = formatted(chapter['starter'])
        chapter['checkTarget'] = chapter['id']
        files[chapter['file']] = chapter['starter']
        chapters.append(chapter)
    for original in PI_LESSONS:
        chapter = dict(original)
        path = 'mini_pi/' + chapter['target'] + '.py'
        chapter.update(file=path, phase='project', mode='deterministic',
                       example=reference[path], checkTarget=chapter['target'],
                       question='请先阅读 hello.py，再把问候语改为中文。')
        chapter['starter'] = focused_starter(reference[path], chapter['focus'])
        files[path] = chapter['starter']
        chapters.append(chapter)
    path = 'mini_pi/project.py'
    starter = focused_starter(reference[path], 'assembly')
    files[path] = starter
    chapters.append(dict(
        id='project', group='扩展与组装', title='运行自己组装的 mini-pi',
        phase='project', mode='model', live=True, file=path,
        checkTarget='project', example=reference[path], starter=starter,
        question='请阅读 hello.py，把问候语改成中文，并运行检查。',
        lesson='''现在把前面完成的关键函数放到同一个项目中。`MiniPi` 是已经提供的装配外壳，它会调用你的模型创建、文件编辑、工具分发、窗口上下文、会话分支、图连接和预算检查。你可以在文件栏打开它，沿着导入语句找到自己实现的函数。\n\n```text\n模型接口 → Agent 循环 → 工具分发 → 文件操作\n              ↕\n上下文、会话、检查点、技能与运行事件\n```\n\n最后补全 `build_project(root, data, model, on_event)`，返回配置好的 MiniPi。`root` 是代码工作目录，`data` 保存会话和检查点，`model` 可以是真实模型或检查用替身，`on_event` 接收运行过程。\n\n```python\nagent = build_project(\n    root="workspace",\n    data=".mini-pi",\n)\ntry:\n    result = agent.run("阅读 hello.py，解释它的作用。")\nfinally:\n    agent.close()\n```\n\n先运行离线检查，确认整个项目能读取、修改、暂停确认和恢复，再填写模型配置尝试自己的任务。修改请求会先显示出来，确认以后才执行。这个 Python 项目复现 Pi 的核心运行方式，原项目的终端渲染和完整扩展生态可以作为下一步阅读源码的目标。''',
        task='完成 build_project，把参数传给 MiniPi，启用修改前确认和窗口上下文，然后运行整个项目。',
        success='当 Agent 先读出代码，提出修改，得到确认后保存文件并检查结果，你就把前面实现的组件组装成了一个可以工作的编程 Agent。',
        hints=['传入 model 时直接使用它，检查会注入固定模型验证运行过程。', '返回 MiniPi 实例，不要在 build_project 内提前执行用户任务。']))
    files['mini_pi/cli.py'] = reference['mini_pi/cli.py']
    chapters[-1]['lesson'] += '\n\n右侧已经接好事件转发：`encode_event(event)` 把事件编码成一行 JSON，`EventDecoder.feed()` 将它恢复为事件，`display()` 再调用显示回调。这会实际使用你在事件任务里完成的函数。最后将 `root`、`data`、`model` 和 `display` 交给 MiniPi 即可，参考实现中的构造参数已经逐行列出。'
    groups = list(dict.fromkeys(ch['group'] for ch in chapters))
    if set(SPECS) != {ch['id'] for ch in chapters}:
        raise ValueError('任务接口说明必须覆盖全部课程')
    if set(NOTES) != {ch['id'] for ch in chapters}:
        raise ValueError('组件用法说明必须覆盖全部课程')
    if set(PREVIEWS) != {ch['id'] for ch in chapters}:
        raise ValueError('测试输入字段必须覆盖全部课程')
    for ch in chapters:
        ch['interface'] = SPECS[ch['id']]
        ch['panelInputs'] = PREVIEWS[ch['id']]
        if ch['live']:
            ch['inputLabel'] = LIVE_INPUT.get(ch['id'],'question')
            ch['runtimeOutput'] = RUNTIME_OUTPUT[ch['id']]
        ch['referenceCode'] = ch['example']
        if ch['phase'] == 'project':
            focus = ch.get('focus', 'build_project')
            if focus == 'edges':
                focus = 'build_graph'
            node = ast.parse(ch['example'])
            for name in focus.split('.'):
                node = next(item for item in node.body if getattr(item, 'name', None) == name)
            ch['referenceCode'] = formatted(ast.unparse(node))
        ch['lesson'] = enrich(ch['id'], ch['lesson'])
        for snippet in re.findall(r'```python\n(.*?)```', ch['lesson'], re.S):
            ast.parse(snippet, filename=ch['id'] + ' example')
        ch['documentedImports'] = audit_components(ch)
        ch.setdefault('live', False)
        ch['referenceFiles'] = [ch['file']]
        if ch['id'] in {'weather_tool','weather_agent'}:
            ch['referenceFiles'] += ['practice/weather_support.py','practice/weather_cities.csv']
        if ch['id']=='weather_tool':
            ch.update(inputLabel='city',inputAria='城市名称',requiresModel=False)
        specification = ch['interface']
        explanations = [p['description'] for p in specification['parameters']]
        for value in [ch['lesson'],ch['task'],ch['success'],*ch['hints'],specification['returns'],*specification['requirements'],specification['example']['explanation'],*explanations]:
            prose=re.sub(r'```.*?```','',value,flags=re.S)
            if any(word in prose for word in ['一句话','不是','而是','；',';','只做一件事','暂时不需要','本节依据','这一节根据《','根据你的要求','根据您的要求','笔记本中的','04_LLM工具封装与调用']):
                raise ValueError('请改写课程表达：'+ch['id'])
    data = dict(version=3, title='Agent 从 0 到 1', project='mini-pi',
                introductionSource='docs/01-Agent基础与进阶.md', groups=groups,
                chapters=chapters, files=files)
    (ROOT/'oj/agent_course.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    build()
