"""Behavioral component checks. Model output prose is never an answer oracle."""
import asyncio
import importlib
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from agent_display import capture_call,target_name,attach
ASYNC_LOOP=asyncio.new_event_loop()
COURSE_V3=json.loads(Path(__file__).with_name('agent_course.json').read_text(encoding='utf-8'))
LESSONS={chapter['id']:chapter for chapter in COURSE_V3['chapters']}


class ScriptedModel:
    def __init__(self, answers=()):
        self.answers = list(answers)
        self.requests = []
        self.tools = []
    def bind_tools(self, tools):
        self.tools = list(tools)
        return self
    def invoke(self, messages):
        self.requests.append(list(messages))
        if not self.answers:
            raise AssertionError('发生了多余的模型调用')
        return self.answers.pop(0)
    def stream(self, messages):
        answer = self.invoke(messages)
        if answer.tool_calls:
            yield AIMessageChunk(content=answer.content, tool_calls=answer.tool_calls)
        else:
            yield AIMessageChunk(content=answer.content[:1])
            yield AIMessageChunk(content=answer.content[1:], usage_metadata={'input_tokens': 2, 'output_tokens': 3, 'total_tokens': 5})


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(error_type, fn):
    try:
        fn()
    except error_type:
        return
    raise AssertionError(f'应该抛出 {error_type.__name__}')


def call(name, args, ident='call-1'):
    return AIMessage(content='', tool_calls=[{'name': name, 'args': args, 'id': ident, 'type': 'tool_call'}])


def check(chapter_id, example_only=False):
    chapter=LESSONS.get(chapter_id)
    if chapter and chapter.get('phase')=='foundation':
        from beginner_checks import check as check_beginner
        return check_beginner(chapter_id,ASYNC_LOOP,example_only=example_only,chapter=chapter)
    if chapter_id=='project':
        for prerequisite in COURSE_V3['chapters']:
            if prerequisite.get('phase')=='project' and prerequisite['id']!='project':
                result=check(prerequisite['id'])
                require(result['verdict']=='AC',f"请先完成「{prerequisite['title']}」，它的检查尚未通过。")
        from mini_pi.project import build_project
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root=Path(folder)/'workspace';root.mkdir()
            (root/'hello.py').write_text('print("hello")',encoding='utf-8')
            model=ScriptedModel([call('read',{'path':'hello.py'}),AIMessage(content='已读文件')])
            events=[]
            with capture_call('mini_pi.project','build_project') as snapshot:
                agent=build_project(root,Path(folder)/'data',model,events.append)
            try:
                result=agent.run('解释 hello.py')
                require(len(model.requests)==2,'组装后的 Agent 没有完成工具循环')
                require(any(event['type']=='tool_end' for event in events),'工具事件没有传出')
                require(result['messages'][-1].content=='已读文件','没有返回模型最后的回答')
            finally:agent.close()
        return {'verdict':'AC','passed':1,'total':1,'cases':[{'name':'自己的组件完成读取与回答','status':'passed','public':True,**attach(snapshot,chapter)}]}
    if chapter:chapter_id=chapter['checkTarget']
    module = importlib.import_module('mini_pi.' + chapter_id)
    cases = []
    def case(name, run):
        if example_only and cases:return
        snapshot={}
        try:
            with capture_call(module.__name__,target_name(chapter or {})) as snapshot:
                run()
            cases.append({'name': name, 'status': 'passed', 'public': True})
        except Exception as error:
            cases.append({'name': name, 'status': 'failed', 'public': True, 'message': f'{type(error).__name__}: {error}'})
        cases[-1].update(attach(snapshot,chapter or {}))
        if cases[-1]['status']!='passed' and cases[-1].get('actual')=='None':cases[-1].pop('actual',None)

    with tempfile.TemporaryDirectory(dir=Path.cwd(), prefix='checks-') as directory:
        root = Path(directory)
        if chapter_id == 'config':
            def provider(prefix, name, base):
                file = root / '.env'
                file.write_text(f'MODEL_PROVIDER={name}\n{prefix}_API_KEY=fixture\n{prefix}_MODEL=test-model\n', encoding='utf-8')
                value = module.load_config(file)
                require(value['api_key'] == 'fixture' and value['model'] == 'test-model' and value['base_url'].rstrip('/') == base, '配置字段未正确读取')
                with patch.object(module, 'ChatOpenAI') as factory:
                    module.create_model(value)
                    require(factory.call_args.kwargs['api_key'] == 'fixture' and factory.call_args.kwargs['base_url'] == value['base_url'], '模型没有使用配置中的连接信息')
            case('OpenAI 配置', lambda: provider('OPENAI', 'openai', 'https://api.openai.com/v1'))
            case('智谱配置', lambda: provider('ZHIPUAI', 'zhipu', 'https://open.bigmodel.cn/api/paas/v4'))
            def missing():
                file = root/'.env'; file.write_text('MODEL_PROVIDER=openai\n', encoding='utf-8')
                raises(ValueError, lambda: module.load_config(file))
                file.write_text('MODEL_PROVIDER=unknown\n', encoding='utf-8')
                raises(ValueError, lambda: module.load_config(file))
            case('缺失字段和未知厂商', missing)
            def generic():
                path=root/'.env';path.write_text('MODEL_PROVIDER=custom\nMODEL_API_KEY=fixture\nMODEL_NAME=custom-model\nMODEL_BASE_URL=https://fixture.invalid/v1\n')
                config=module.load_config(path)
                require(config['model']=='custom-model' and config['base_url']=='https://fixture.invalid/v1','通用字段或自定义地址没有使用')
            case('通用配置与自定义服务',generic)
        elif chapter_id == 'messages':
            def history():
                old = [HumanMessage(content='旧问题'), AIMessage(content='旧回答')]
                messages = module.make_messages('新问题', old, '系统说明')
                require([m.type for m in messages] == ['system','human','ai','human'], '消息角色或顺序不正确')
                require(messages[0].content == '系统说明' and len(old) == 2, '系统说明或输入历史被改动')
            case('消息角色、历史与输入不变', history)
            def invoke():
                model = ScriptedModel([AIMessage(content='任意回答')])
                result = module.ask(model, '你好')
                require(isinstance(result, AIMessage) and len(model.requests) == 1 and model.requests[0][-1].content == '你好', '没有通过模型获取助手消息')
            case('真实调用接口而不比较措辞', invoke)
            case('空问题', lambda: raises(ValueError, lambda: module.make_messages('   ')))
        elif chapter_id == 'streaming':
            def text():
                shown=[]
                result=module.collect_stream(iter([AIMessageChunk(content='你'),AIMessageChunk(content='好')]), shown.append)
                require(result.content == '你好' and shown == ['你','好'], '文本片段丢失或没有逐段通知')
                require(module.text_of(AIMessage(content=[{'type':'text','text':'a'},{'type':'image_url','image_url':{'url':'x'}}])) == 'a', '内容块文本提取错误')
            case('文本与内容块逐段拼接', text)
            def tools():
                chunks=[AIMessageChunk(content='',tool_call_chunks=[{'name':'read','args':'{"path":','id':'a','index':0}]),
                        AIMessageChunk(content='',tool_call_chunks=[{'name':None,'args':'"hello.py"}','id':None,'index':0}])]
                result=module.collect_stream(chunks)
                require(result.tool_calls[0]['args'] == {'path':'hello.py'} and result.tool_calls[0]['id']=='a','工具参数片段未正确聚合')
            case('跨片段的工具调用参数',tools)
            case('空流与停止',lambda:(raises(ValueError,lambda:module.collect_stream(iter([]))),raises(InterruptedError,lambda:module.collect_stream(iter([AIMessageChunk(content='a')]),cancelled=lambda:True))))
            async def async_check():
                async def chunks():
                    yield AIMessageChunk(content='异')
                    yield AIMessageChunk(content='步')
                shown=[];result=await module.collect_async(chunks(),shown.append)
                require(result.content=='异步' and shown==['异','步'],'异步聚合不正确')
            case('异步流',lambda:ASYNC_LOOP.run_until_complete(async_check()))
        elif chapter_id == 'responses':
            def structured():
                value=module.Review(filename='a.py',issues=[])
                class Model:
                    def with_structured_output(self,schema,**kwargs):
                        require(schema is module.Review,'没有使用 Review schema');return self
                    def invoke(self,text):return value
                require(module.review(Model(),'检查') is value,'未返回类型化结果')
            case('结构化结果',structured)
            def retry():
                count=[];wait=[]
                def operation():
                    count.append(1)
                    if len(count)<3:raise TimeoutError('fixture')
                    return 'done'
                require(module.retry_call(operation,sleep=wait.append)=='done' and len(count)==3 and wait==[1,2],'重试或等待不正确')
                raises(ValueError,lambda:module.retry_call(lambda:(_ for _ in ()).throw(ValueError('bad')),sleep=wait.append))
                raises(TimeoutError,lambda:module.retry_call(lambda:(_ for _ in ()).throw(TimeoutError()),sleep=lambda _:None))
            case('可恢复失败、退避与最终异常',retry)
        elif chapter_id == 'files':
            def files():
                module.write_file(root,'sub/a.py','hello world')
                module.edit_file(root,'sub/a.py','hello','你好')
                require(module.read_file(root,'sub/a.py')=='你好 world','文件读写或替换不正确')
            case('读取、写入与唯一替换',files)
            def repeat():
                module.write_file(root,'repeat.txt','xx xx')
                raises(ValueError,lambda:module.edit_file(root,'repeat.txt','xx','y'))
                raises(ValueError,lambda:module.edit_file(root,'repeat.txt','','y'))
                require(module.read_file(root,'repeat.txt')=='xx xx','拒绝后文件被改变')
            case('重复匹配与空目标',repeat)
            case('越界路径与 .env',lambda:(raises(ValueError,lambda:module.workspace_path(root,'../outside.txt')),raises(ValueError,lambda:module.workspace_path(root,'.env'))))
        elif chapter_id=='models':
            def registry():
                r=module.ModelRegistry();received=[]
                r.register('one',lambda config:received.append(config) or 'first',[{'name':'m','tools':True}])
                r.register('two',lambda config:'second',[{'name':'m','tools':False}])
                require(r.create('one','m',{'api_key':'fixture'})=='first' and received[0]['model']=='m' and len(r.list_models())==2,'目录、选择或工厂参数错误')
                raises(ValueError,lambda:r.create('two','m',{}));raises(ValueError,lambda:r.register('one',lambda _:None,[]))
            case('多厂商注册、选择与能力',registry)
        elif chapter_id=='limits':
            def budget():
                b=module.Budget(2,10);b.before_call();b.record({'total_tokens':10})
                raises(RuntimeError,b.before_call)
                other=module.Budget(1,100);other.before_call();raises(RuntimeError,other.before_call)
                require(module.truncate_output('abcdef',3).startswith('abc') and '截断' in module.truncate_output('abcdef',3),'裁剪未标明丢失内容')
                require(module.estimate_tokens([HumanMessage(content='你好')])>=2,'估计没有考虑中文')
            case('请求与用量上限、裁剪与估计',budget)
        elif chapter_id=='diffs':
            def preview():
                from mini_pi.files import write_file,read_file
                write_file(root,'a.py','old\n');p=module.preview_edit(root,'a.py','old','new')
                require(read_file(root,'a.py')=='old\n' and '-old' in p['patch'] and '+new' in p['patch'],'预览已写入或差异错误')
                module.apply_preview(root,p);module.undo_preview(root,p);require(read_file(root,'a.py')=='old\n','撤销没有恢复')
                write_file(root,'a.py','later\n');raises(ValueError,lambda:module.apply_preview(root,p));raises(ValueError,lambda:module.undo_preview(root,p))
            case('无副作用预览、应用、撤销与冲突',preview)
        elif chapter_id=='commands':
            def command():
                (root/'a.py').write_text('print("hello")')
                with patch.object(module.subprocess,'run',return_value=subprocess.CompletedProcess([],2,'out','err')) as run:
                    result=module.run_python(root,'a.py',3)
                    require(result=={'returncode':2,'stdout':'out','stderr':'err'},'退出码或输出错误')
                    require(run.call_args.kwargs['shell'] is False and run.call_args.kwargs['timeout']==3 and run.call_args.args[0][1]=='-I','命令参数或超时错误')
                with patch.object(module.subprocess,'run',side_effect=subprocess.TimeoutExpired('python',1)):
                    raises(subprocess.TimeoutExpired,lambda:module.run_python(root,'a.py',1))
                raises(ValueError,lambda:module.run_python(root,'a.txt'))
            case('命令参数、输出、非零退出与超时',command)
        elif chapter_id=='instructions':
            def instructions():
                (root/'AGENTS.md').write_text('root instructions');(root/'src'/'sub').mkdir(parents=True)
                (root/'src'/'AGENTS.md').write_text('src instructions');(root/'src'/'sub'/'a.py').write_text('x')
                value=module.project_instructions(root,'src/sub/a.py')
                require(value.count('root instructions')==1 and value.index('root instructions')<value.index('src instructions'),'说明层级或重复读取错误')
                raises(ValueError,lambda:module.project_instructions(root,'../outside'))
            case('层级顺序、来源与项目边界',instructions)
        elif chapter_id=='attachments':
            def attachments():
                (root/'a.txt').write_text('content');(root/'a.png').write_bytes(b'\x89PNG\r\n\x1a\nfixture-image')
                require('content' in module.text_attachment(root,'a.txt')['text'],'文本内容丢失')
                value=module.image_attachment(root,'a.png');require(value['image_url']['url'].startswith('data:image/png;base64,'),'图片块格式错误')
                raises(ValueError,lambda:module.image_attachment(root,'a.txt'))
            case('文本来源、图片格式与类型检查',attachments)
        elif chapter_id == 'tools':
            def execute():
                (root/'a.py').write_text('hello')
                tools=module.make_tools(root);events=[]
                message=AIMessage(content='',tool_calls=[{'name':'read','args':{'path':'a.py'},'id':'a','type':'tool_call'},
                                                         {'name':'edit','args':{'path':'a.py','old':'hello','new':'hi'},'id':'b','type':'tool_call'}])
                result=module.execute_calls(message,tools,events.append)
                require([m.tool_call_id for m in result]==['a','b'] and result[0].content=='hello' and (root/'a.py').read_text()=='hi','多工具执行或 ID 对应错误')
                require([e['type'] for e in events]==['tool_start','tool_end','tool_start','tool_end'],'事件顺序错误')
            case('多个调用、结果 ID 和事件',execute)
            def failure():
                result=module.execute_calls(call('unknown',{}),module.make_tools(root))
                require(result[0].status=='error' and result[0].tool_call_id=='call-1','工具错误没有回传原 ID')
                invalid=module.execute_calls(call('read',{}),module.make_tools(root))
                require(invalid[0].status=='error','参数错误被吞掉')
            case('未知工具与错误参数',failure)
        elif chapter_id == 'loop':
            def loop():
                from mini_pi.tools import make_tools
                (root/'a.py').write_text('hello')
                old=[HumanMessage(content='解释')];model=ScriptedModel([call('read',{'path':'a.py'}),AIMessage(content='任意解释')])
                result=module.agent_loop(model,make_tools(root),old)
                require(len(old)==1 and len(result)==4 and model.requests[1][-1].content=='hello','工具结果未进入第二次请求或输入被修改')
            case('模型 → 工具 → 模型',loop)
            case('轮数上限',lambda:raises(RuntimeError,lambda:module.agent_loop(ScriptedModel([call('unknown',{})]*4),[],[HumanMessage(content='x')],max_rounds=2)))
        elif chapter_id == 'context':
            history=[SystemMessage(content='系统'),HumanMessage(content='旧问题'),call('read',{'path':'x'}),ToolMessage(content='结果',tool_call_id='call-1'),AIMessage(content='旧答'),HumanMessage(content='新问题')]
            def window():
                result=module.window_context(history,1)
                require([m.content for m in result]==['系统','新问题'],'窗口没有按完整轮次裁剪')
                require(len(module.window_context(history,2))==6,'工具请求或结果丢失')
            case('完整轮次与工具配对',window)
            def summary():
                model=ScriptedModel([AIMessage(content='任意摘要')])
                result=module.summary_context(model,history,1)
                require(len(model.requests)==1 and '旧问题' in model.requests[0][-1].content and '新问题' not in model.requests[0][-1].content,'摘要范围不正确')
                require(result[-1] is history[-1] and len(history)==6,'近期历史或原始历史被改动')
            case('摘要只处理旧历史',summary)
        elif chapter_id == 'sessions':
            def branches():
                path=root/'session.jsonl';session=module.Session(path)
                a=session.append(HumanMessage(content='a'));b=session.append(AIMessage(content='b'),a);c=session.append(AIMessage(content='c'),a)
                other=module.Session(path)
                require([m.content for m in other.branch(b)]==['a','b'] and [m.content for m in other.branch(c)]==['a','c'],'重开后分支不正确')
                raises(ValueError,lambda:other.append(AIMessage(content='x'),'missing'))
                raises(ValueError,lambda:other.branch('missing'))
            case('追加、重开和独立分支',branches)
            def tools():
                s=module.Session(root/'tools.jsonl');leaf=s.append(call('read',{'path':'x'},'original'))
                require(s.branch(leaf)[0].tool_calls[0]['id']=='original','持久化丢失工具信息')
            case('工具调用完整保存',tools)
        elif chapter_id == 'memory':
            def memory():
                path=root/'memory.sqlite3';m=module.Memory(path)
                m.put('u','k',{'value':1});m.put('u','k',{'value':2});m.put('other','k',"'quoted'");m.close()
                m=module.Memory(path)
                require(m.get('u','k')=={'value':2} and m.get('other','k')=="'quoted'" and m.get('x','k') is None,'记忆更新、隔离或重开错误');m.close()
            case('更新、隔离、参数和重开',memory)
        elif chapter_id in {'graph','approval'}:
            from mini_pi.tools import make_tools
            from mini_pi.graph import build_graph
            def graph_check():
                (root/'a.py').write_text('old');events=[];model=ScriptedModel([call('read',{'path':'a.py'}),AIMessage(content='已读'),AIMessage(content='另一个线程')])
                graph=build_graph(model,make_tools(root),InMemorySaver(),events.append)
                config={'configurable':{'thread_id':'one'}}
                result=graph.invoke({'messages':[HumanMessage(content='读')],'rounds':0},config)
                require(result['messages'][-1].content=='已读' and result['rounds']==2,'图路由不正确')
                require(any(e['type']=='text' for e in events) and any(e['type']=='tool_end' for e in events),'事件没有贯穿图')
                graph.invoke({'messages':[HumanMessage(content='other')],'rounds':0},{'configurable':{'thread_id':'two'}})
                require(len(model.requests[-1])==1,'线程之间混入了消息')
            def approval(approved):
                from mini_pi.approval import confirm_tools, resume_graph
                (root/'a.py').write_text('old');model=ScriptedModel([call('edit',{'path':'a.py','old':'old','new':'new'}),AIMessage(content='结束')])
                graph=build_graph(model,make_tools(root),InMemorySaver(),before_tools=confirm_tools)
                config={'configurable':{'thread_id':'approval'}}
                result=graph.invoke({'messages':[HumanMessage(content='改')],'rounds':0},config)
                require(result.get('__interrupt__') and (root/'a.py').read_text()=='old','确认前已经产生修改')
                if approved:
                    resume_graph(graph,'approval',True)
                    require((root/'a.py').read_text()=='new','确认后没有修改')
                else:
                    resume_graph(graph,'approval',False)
                    require((root/'a.py').read_text()=='old','取消后仍修改了文件')
            if chapter_id=='graph':
                case('路由、流事件与线程隔离',graph_check)
                case('最大调用轮数',lambda:raises(RuntimeError,lambda:build_graph(ScriptedModel([call('unknown',{})]*5),[],InMemorySaver(),max_rounds=2).invoke({'messages':[HumanMessage(content='x')],'rounds':0},{'configurable':{'thread_id':'limit'}})))
            else:
                case('确认后执行',lambda:approval(True));case('拒绝后不执行',lambda:approval(False))
        elif chapter_id=='controls':
            def queues():
                c=module.Control();c.enqueue('a');c.enqueue('b');c.enqueue('later','followup')
                require([m.content for m in c.take()]==['a','b'] and c.take()==[] and [m.content for m in c.take('followup')]==['later'],'队列顺序或隔离错误')
                c.cancel();require(c.stop.is_set(),'停止标志未设置')
                raises(ValueError,lambda:c.enqueue('','steer'))
            case('队列隔离、顺序与停止',queues)
        elif chapter_id=='skills':
            def skill():
                path=root/'review'/'SKILL.md';path.parent.mkdir();path.write_text('# 审查\n检查边界\n全文',encoding='utf-8')
                catalog=module.discover_skills(root);require('review' in catalog and catalog['review']['description']=='检查边界','技能目录错误')
                require(module.skill_tool(root).invoke({'name':'review'})==path.read_text(encoding='utf-8'),'技能全文未按需加载')
                require(module.expand_prompt('检查 {file}',{'file':'x'})=='检查 x','模板替换错误')
            case('技能目录、全文与模板',skill)
            def hooks():
                hooks=module.Hooks();received=[]
                hooks.on('x',lambda e:e.update(type='changed'));hooks.on('x',received.append);hooks.emit({'type':'x'})
                require(received==[{'type':'x'}],'回调相互修改了事件')
            case('事件回调隔离',hooks)
        elif chapter_id=='telemetry':
            def trace():
                path=root/'trace.jsonl';t=module.Trace(path)
                original={'type':'model_end','usage':{'total_tokens':5},'config':{'api_key':'fixture','nested':[{'secret':'hidden'}]}}
                t.record(original);t.record({'type':'tool_end'})
                rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
                require(t.tokens==5 and len(rows)==2 and rows[0]['config']['api_key']=='[redacted]' and rows[0]['config']['nested'][0]['secret']=='[redacted]','记录、用量或递归脱敏错误')
                require(original['config']['api_key']=='fixture','修改了原始事件')
            case('事件顺序、用量与嵌套脱敏',trace)
        elif chapter_id=='retrieval':
            def search():
                (root/'a.py').write_text('stream stream');(root/'b.md').write_text('stream');(root/'.env').write_text('stream stream stream')
                result=module.search_files(root,'stream',1)
                require(len(result)==1 and result[0]['path']=='a.py' and result[0]['score']==2,'排序或范围错误')
                require(module.search_files(root,'',5)==[],'空查询未返回空结果')
                require(module.search_tool(root).invoke({'query':'stream'})[0]['path']=='a.py','检索工具未接线')
            case('过滤、排序、限制与工具',search)
            def vectors():
                class Embeddings:
                    def embed_documents(self,texts):return [[1,0] if 'code' in text else [0,1] for text in texts]
                    def embed_query(self,text):return [1,0]
                index=module.VectorIndex(Embeddings());index.add('a.py','code');index.add('b.md','notes')
                require(index.search('x',1)==[{'path':'a.py','text':'code'}],'向量检索或来源错误')
                raises(ValueError,lambda:index.add('x','text',5,5))
            case('向量分块、检索与来源',vectors)
        elif chapter_id=='events':
            def events():
                encoded=module.encode_event({'type':'text','text':'你好'});d=module.EventDecoder()
                require(d.feed(encoded[:5])==[],'半行提前返回');result=d.feed(encoded[5:]+encoded)
                require(len(result)==2 and result[0]['text']=='你好','多行或中文解码错误');d.finish()
                d.feed('{');raises(ValueError,d.finish)
            case('半行、多行、中文与残缺结束',events)
        elif chapter_id=='mcp':
            async def mcp():
                observed=[]
                class Adapter:
                    def __init__(self,target):observed.append(target)
                    async def __aenter__(self):observed.append('enter');return self
                    async def list_tools(self):observed.append('list');return ['tool']
                    async def __aexit__(self,*args):observed.append('exit')
                result=await module.load_mcp_tools('https://fixture.invalid/mcp',Adapter)
                require(result==['tool'] and observed[-3:]==['enter','list','exit'],'MCP 生命周期或工具发现错误')
            case('异步连接、工具发现与退出',lambda:ASYNC_LOOP.run_until_complete(mcp()))
        elif chapter_id=='evaluation':
            def evaluation():
                result=module.evaluate_run([{'type':'tool_end','name':'read','status':'success'},{'type':'model_end'}],['read'],{'a':'x'},{'a':'x'})
                require(result['passed'] and result['model_calls']==1,'组合评估错误')
                require(not module.evaluate_run([{'type':'tool_end','name':'read','status':'error'}],['read'],{}, {})['passed'],'失败工具误判通过')
            case('成功轨迹、实际文件与组合结果',evaluation)
        elif chapter_id=='rpc':
            def rpc():
                observed=[]
                class Control:
                    def enqueue(self,text,kind):observed.append((text,kind))
                    def cancel(self):observed.append('cancel')
                class Agent:
                    control=Control()
                    def run(self,text,thread,attachments=()):observed.append((text,thread));return {'messages':[]}
                r=module.AgentRPC(Agent());value=r.handle({'id':'one','command':'prompt','params':{'text':'question','thread_id':'thread'}})
                require(value['id']=='one' and value['ok'] and observed==[('question','thread')],'请求分发或 ID 错误')
                r.handle({'command':'steer','params':{'text':'adjust'}});r.handle({'command':'cancel'})
                require(observed[-2:]==[('adjust','steer'),'cancel'],'控制命令未接通')
                require(not r.handle({'id':'bad','command':'unknown'})['ok'],'未知命令未封装错误')
            case('请求分发、事件控制与错误封装',rpc)
        elif chapter_id=='app':
            def app():
                path=root/'work';path.mkdir();(path/'hello.py').write_text('old')
                model=ScriptedModel([call('read',{'path':'hello.py'},'read'),call('edit',{'path':'hello.py','old':'old','new':'new'},'edit'),AIMessage(content='任意完成说明'),AIMessage(content='继续'),AIMessage(content='分支')])
                events=[];agent=module.MiniPi(path,root/'data',model,events.append)
                agent.memory.put('user','preferences',{'language':'zh'})
                result=agent.run('先读再改')
                require(result.get('__interrupt__') and (path/'hello.py').read_text()=='old','端到端未等待确认')
                agent.resume(True)
                require((path/'hello.py').read_text()=='new' and len(agent.session.entries)>=6,'工具修改或会话记录未完成')
                leaf=agent.session.entries[1]['id'];agent.fork(leaf,'branch');agent.run('继续','main');agent.run('另一方案','branch')
                require(len(events)>4 and 'zh' in agent.prompt().content and agent.trace.tokens>0,'偏好、记录或显示回调未接通')
                agent.close()
                reopened=module.MiniPi(path,root/'data',ScriptedModel([AIMessage(content='重开')]))
                old_count=len(reopened.session.entries);reopened.run('重开后的问题');require(len(reopened.session.entries)>old_count,'重开后没有继续记录');reopened.close()
            case('读文件 → 修改确认 → 恢复 → 续聊 → 分支 → 重开',app)
        elif chapter_id=='cli':
            def cli():
                work=root/'work';work.mkdir();(work/'hello.py').write_text('hello')
                with patch('sys.argv',['mini-pi','--demo','--root',str(work),'--data',str(root/'data'),'--no-stream']):
                    module.main()
                require((root/'data'/'session.jsonl').exists(),'CLI 没有运行 Agent 或保存会话')
            case('离线 CLI 真实运行与关闭',cli)
        else:
            raise ValueError('未知组件')
    passed=sum(c['status']=='passed' for c in cases)
    return {'verdict':'AC' if passed==len(cases) and cases else 'WA','passed':passed,'total':len(cases),'cases':cases}


def live_run(payload, emit, data_root):
    chapter=payload['chapterId'];question=payload.get('question') or '请解释 hello.py 的功能'
    metadata=LESSONS.get(chapter,{})
    if metadata.get('phase')=='foundation':
        from beginner_checks import live
        if metadata.get('requiresModel') is False:
            return live(chapter,payload,emit,None,{})
        from dotenv import dotenv_values
        from langchain_openai import ChatOpenAI
        values=dotenv_values('.env',interpolate=False)
        provider=values.get('MODEL_PROVIDER') or 'openai'
        prefix='ZHIPUAI' if provider=='zhipu' else 'OPENAI'
        config={'model':values.get('MODEL_NAME') or values.get(prefix+'_MODEL'),
                'api_key':values.get('MODEL_API_KEY') or values.get(prefix+'_API_KEY'),
                'base_url':values.get('MODEL_BASE_URL') or values.get(prefix+'_BASE_URL') or ('https://open.bigmodel.cn/api/paas/v4/' if provider=='zhipu' else 'https://api.openai.com/v1')}
        if not config['model'] or not config['api_key']:raise ValueError('请打开 .env，填写模型名称与 API Key。')
        def make_model(config):
            options={'timeout':30,'max_retries':2,'use_responses_api':False,'stream_usage':False,**config}
            return ChatOpenAI(**options)
        return live(chapter,payload,emit,make_model,config)
    from mini_pi.config import load_config, create_model
    model=create_model(load_config('.env'))
    observed={'calls':0,'chunks':0}
    invoke=model.invoke if hasattr(model,'invoke') else None
    stream=model.stream if hasattr(model,'stream') else None
    if invoke:
        def watched_invoke(*args,**kwargs):
            observed['calls']+=1
            return invoke(*args,**kwargs)
        object.__setattr__(model,'invoke',watched_invoke)
    if stream:
        def watched_stream(*args,**kwargs):
            observed['calls']+=1
            for chunk in stream(*args,**kwargs):
                observed['chunks']+=1
                yield chunk
        object.__setattr__(model,'stream',watched_stream)
    if chapter=='messages':
        from mini_pi.messages import ask
        result=ask(model,question)
        require(isinstance(result,AIMessage),'调用应该返回 AIMessage')
        require(observed['calls']>0,'没有调用传入的模型，请通过模型接口获得回答')
        text=result.content if isinstance(result.content,str) else ''.join(b.get('text','') for b in result.content if b.get('type')=='text')
        emit({'type':'text','text':text})
    elif chapter=='streaming':
        from mini_pi.messages import make_messages
        from mini_pi.streaming import collect_stream
        result=collect_stream(model.stream(make_messages(question)),lambda text:emit({'type':'text','text':text}))
        require(isinstance(result,AIMessage),'流聚合应该返回完整助手消息')
        require(observed['calls']>0 and observed['chunks']>0,'没有消费模型流式片段')
    elif chapter in {'app','project'}:
        from mini_pi.project import build_project
        root=Path.cwd()/'workspace'
        # Live tool edits affect only this run's snapshot and are returned as file diffs.
        agent=build_project(root,data_root,model,emit)
        try:
            if payload.get('approval') is not None:
                result=agent.resume(payload['approval'],payload.get('threadId','main'))
            else:
                result=agent.run(question,payload.get('threadId','main'))
            require(observed['calls']>0,'Agent 没有调用模型接口')
            changed={p.relative_to(Path.cwd()).as_posix():p.read_text(encoding='utf-8') for p in root.rglob('*') if p.is_file() and p.suffix in {'.py','.md','.txt'} and p.stat().st_size<=100000}
            if result.get('__interrupt__'):
                return {'verdict':'WAITING','message':'等待确认','interrupt':result['__interrupt__'][0].value,'cases':[],'changedFiles':changed}
            return {'verdict':'OK','message':'功能运行完成','cases':[],'changedFiles':changed}
        finally:
            agent.close()
    else:
        raise ValueError('当前组件使用离线检查')
    return {'verdict':'OK','message':'模型调用完成','cases':[]}
