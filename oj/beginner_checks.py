"""Behavior checks for short lessons, with real LangChain/LangGraph objects."""
import importlib
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from agent_display import capture_call,target_name,attach,chapters

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from typing_extensions import TypedDict


class ReplyModel(BaseChatModel):
    calls: list = []
    use_tools: bool = False
    bound_names: list = []

    @property
    def _llm_type(self):
        return 'lesson-fixture'

    def bind_tools(self, tools, **kwargs):
        self.bound_names = [tool.name for tool in tools]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(list(messages))
        if self.use_tools and not isinstance(messages[-1], ToolMessage):
            answer = AIMessage(content='', tool_calls=[{
                'name': 'get_weather', 'args': {'city': '杭州'},
                'id': 'weather-1', 'type': 'tool_call',
            }])
        else:
            answer = AIMessage(content='收到：' + str(messages[-1].content))
        return ChatResult(generations=[ChatGeneration(message=answer)])


@contextmanager
def weather_response(*, temperature=26.5, condition='多云', status=200, body=None, timeout=False, malformed=False):
    """Use the real HTTP client and student parser with an in-process transport."""
    module=importlib.import_module('practice.weather_tool')
    requests=[]
    def respond(request):
        requests.append(request)
        if timeout:raise httpx.ReadTimeout('天气服务超时',request=request)
        if malformed:return httpx.Response(200,content='not-json')
        data=body if body is not None else {'result':{'realtime':{'temp':temperature,'text':condition}}}
        return httpx.Response(status,json=data)
    def get(url,**kwargs):
        with httpx.Client(transport=httpx.MockTransport(respond),trust_env=False) as client:
            return client.get(url,**kwargs)
    config={'url':'https://eolink.o.apispace.com/456456/weather/v001/now','api_key':'weather-fixture-key'}
    with patch.object(module,'load_weather_config',return_value=config),patch.object(httpx,'get',side_effect=get):
        yield requests


def check(identifier, event_loop, example_only=False, chapter=None):
    chapter=chapter or chapters().get(identifier,{})
    module = importlib.import_module('practice.' + identifier)
    cases = []

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def case(name, operation, expected=None, expected_error=None):
        if example_only and cases:
            return
        snapshot={}
        try:
            with capture_call(module.__name__,target_name(chapter)) as snapshot:
                observed=operation()
            if isinstance(observed,dict) and '_displayActual' in observed:snapshot['actual']=observed['_displayActual']
            cases.append({'name': name, 'status': 'passed', 'public': True})
        except Exception as error:
            cases.append({'name': name, 'status': 'failed', 'public': True,
                          'message': f'{type(error).__name__}: {error}'})
        cases[-1].update(attach(snapshot,chapter,expected))
        if expected_error:cases[-1].update(expected=expected_error,expectedLabel='预期异常')
        if cases[-1]['status']!='passed' and cases[-1].get('actual')=='None':cases[-1].pop('actual',None)

    if identifier == 'intro':
        module.demo()
        return {'verdict': 'OK', 'cases': []}
    if identifier == 'first_reply':
        def reply(question):
            model = ReplyModel()
            config = {'model': 'fixture', 'api_key': 'fixture', 'base_url': 'https://fixture.invalid'}
            with patch.object(module, 'ChatOpenAI', return_value=model) as factory:
                answer = module.reply(config, question)
            require(factory.called and all(factory.call_args.kwargs.get(key)==config[key] for key in config), '创建模型时没有使用配置中的型号、密钥或地址')
            require(len(model.calls) == 1, '需要调用模型获得回答')
            require(model.calls[0][-1].content == question,
                    '模型收到的问题与传入的 question 不一致。请直接使用 model.invoke(question)，不要在函数内把 question 改成固定文字。')
            require(answer == '收到：' + question,
                    '问题已正确发送，但返回值与模型回答的 content 不一致。请返回 answer.content。')
        case('传递问题并返回模型内容', lambda: reply('解释一下 Agent'),expected='收到：解释一下 Agent')
        case('更换问题后使用新的输入', lambda: reply('请介绍工具调用'),expected='收到：请介绍工具调用')
    elif identifier == 'stream_reply':
        def streaming(parts):
            used = []
            class Model:
                def stream(self, question):
                    used.append(question)
                    for text in parts:
                        yield AIMessageChunk(content=text)
            shown = []
            result = module.stream_reply(Model(), '问题', shown.append)
            require(used == ['问题'], '没有调用 stream')
            require(result == ''.join(parts), '最终文字拼接不正确')
            require(shown == [part for part in parts if part], '没有逐段显示有效文本')
        case('多段文本逐段出现', lambda: streaming(['你', '好', '，世界']),expected='你好，世界')
        case('忽略空片段但保留其他内容', lambda: streaming(['', 'A', '', 'B']),expected='AB')
    elif identifier == 'prompt_chain':
        def chain():
            model = ReplyModel()
            chain = module.make_chain(model)
            answer = chain.invoke({'topic': '工具调用'})
            require(isinstance(answer, str), '链最后需要返回字符串')
            require(model.calls and '工具调用' in model.calls[0][-1].content, 'topic 没有进入模板')
            chain.invoke({'topic': '记忆'})
            require('记忆' in model.calls[1][-1].content, '模板没有使用这次的新输入')
        case('模板变量、模型与字符串结果', chain)
    elif identifier == 'weather_tool':
        def weather(city,code,temperature,condition):
            with weather_response(temperature=temperature,condition=condition) as requests:
                result=module.get_weather.invoke({'city':city})
            require(len(requests)==1,'需要真实执行一次天气 HTTP 请求，提交时由本地传输层返回响应')
            request=requests[0]
            require(request.url.path=='/456456/weather/v001/now','没有请求配置中的天气接口地址')
            require(request.url.params.get('areacode')==code,'没有使用该城市的编码作为 areacode 参数')
            require(request.headers.get('X-APISpace-Token')=='weather-fixture-key','天气凭证没有放入 X-APISpace-Token 请求头')
            require(request.extensions.get('timeout',{}).get('read')==10,'请将 HTTP 请求的 timeout 设置为 10 秒')
            require(isinstance(result,str) and city in result and str(temperature) in result and condition in result,'需要从本次响应读取城市、天气与温度并返回，不能写死结果')
        def failure(error_type,**options):
            with weather_response(**options):
                try:module.get_weather.invoke({'city':'杭州'})
                except error_type as error:return {'_displayActual':type(error).__name__}
            raise AssertionError('请求失败或响应无效时需要报告异常，不能返回虚构天气')
        def unknown():
            with weather_response() as requests:
                try:module.get_weather.invoke({'city':'不存在的城市xyz'})
                except ValueError:
                    require(not requests,'城市不存在时不应默认查询其他城市')
                    return {'_displayActual':'ValueError'}
            raise AssertionError('未知城市需要明确报错，不能默认查询北京')
        case('杭州请求参数与响应解析',lambda:weather('杭州','101210101',26.5,'多云'),expected='杭州：多云，26.5℃')
        case('更换城市与零度天气',lambda:weather('北京市','101010100',0,'晴'),expected='北京市：晴，0℃')
        case('未知城市不发送错误请求',unknown,expected_error='ValueError')
        case('HTTP 认证失败会报错',lambda:failure(httpx.HTTPStatusError,status=401),expected_error='HTTPStatusError')
        case('请求超时会报错',lambda:failure(httpx.TimeoutException,timeout=True),expected_error='TimeoutException 或其子类')
        case('无效 JSON 会报错',lambda:failure(ValueError,malformed=True),expected_error='ValueError 或其子类')
        case('缺少天气字段会报错',lambda:failure(ValueError,body={'result':{'realtime':{'temp':20}}}),expected_error='ValueError')
    elif identifier == 'weather_agent':
        def agent():
            model = ReplyModel(use_tools=True)
            agent = module.build_agent(model)
            with weather_response(temperature=27.5,condition='小雨') as requests:
                result = agent.invoke({'messages': [{'role': 'user', 'content': '杭州的天气怎么样？'}]})
            messages = result['messages']
            tools = [m for m in messages if isinstance(m, ToolMessage)]
            require(model.bound_names == ['get_weather'], '天气工具没有交给模型')
            require(len(model.calls) >= 2 and tools, '没有完成模型、工具、模型的循环')
            require(requests and '27.5' in tools[0].content and '小雨' in tools[0].content and '27.5' in messages[-1].content, '天气接口结果没有经过工具回到模型')
        case('真实工具执行与结果回传', agent)
    elif identifier == 'structured':
        def structured():
            used = []
            class Model:
                def with_structured_output(self, schema, **kwargs):
                    used.append(schema)
                    return SimpleNamespace(invoke=lambda text: schema(city='杭州', days=3))
            plan = module.extract_plan(Model(), '杭州三天')
            require(used == [module.TravelPlan], '没有使用给定的数据结构')
            require(plan.city == '杭州' and plan.days == 3, '需要返回可读取字段的计划对象')
        case('结构化结果可读取', structured, expected={'city':'杭州','days':3})
    elif identifier == 'conversation':
        def conversation():
            model = ReplyModel()
            original = [HumanMessage(content='我叫小林'), AIMessage(content='你好')]
            result = module.chat(model, original, '我叫什么？')
            require(len(original) == 2, '不要修改传入的旧历史')
            require(len(result) == 4 and len(model.calls[0]) == 3, '旧消息、新问题或回答丢失')
            require(result[-1].type == 'ai' and result[-2].type == 'human', '消息角色或顺序不正确')
        case('历史传入与新一轮保存', conversation)
    elif identifier == 'workflow':
        def workflow():
            model = ReplyModel()
            result = module.build_workflow(model).invoke({'question': '  你好  '})
            require(model.calls[0][-1].content == '你好', '模型没有收到 clean 处理后的问题')
            require(result['answer'] == '收到：你好', '没有返回 answer 节点的结果')
        case('节点按正确顺序运行', workflow)
    elif identifier == 'routing':
        class State(TypedDict):
            need_tool: bool
            route: str
        def routing(flag):
            graph = StateGraph(State)
            graph.add_node('decide', lambda state: {})
            graph.add_node('tools', lambda state: {'route': 'tools'})
            graph.add_node('answer', lambda state: {'route': 'answer'})
            graph.add_edge(START, 'decide')
            graph.add_conditional_edges('decide', module.route)
            graph.add_edge('tools', END)
            graph.add_edge('answer', END)
            result = graph.compile().invoke({'need_tool': flag})
            require(result['route'] == ('tools' if flag else 'answer'), '分支选择不正确')
        case('需要工具时进入 tools', lambda: routing(True), expected='tools')
        case('不需要工具时进入 answer', lambda: routing(False), expected='answer')
    elif identifier == 'checkpoint':
        def checkpoint():
            model = ReplyModel()
            app = module.build_chat(model, InMemorySaver())
            one = {'configurable': {'thread_id': 'one'}}
            two = {'configurable': {'thread_id': 'two'}}
            app.invoke({'messages': [('user', '我叫小林')]}, one)
            app.invoke({'messages': [('user', '我叫什么')]}, one)
            app.invoke({'messages': [('user', '新对话')]}, two)
            require(len(model.calls[1]) == 3, '同一线程没有保留上一轮')
            require(len(model.calls[2]) == 1, '不同线程混入了历史')
        case('连续对话与线程隔离', checkpoint)
    elif identifier == 'approval':
        class State(TypedDict):
            question: str
            approved: bool
        def approval(value):
            graph = StateGraph(State)
            graph.add_node('approve', module.approve)
            graph.add_edge(START, 'approve')
            graph.add_edge('approve', END)
            app = graph.compile(checkpointer=InMemorySaver())
            config = {'configurable': {'thread_id': 'test'}}
            first = app.invoke({'question': '确认吗？'}, config)
            require(first.get('__interrupt__'), '节点没有暂停等待确认')
            second = app.invoke(Command(resume=value), config)
            require(second['approved'] is (value is True), '恢复后的确认结果不正确')
        case('确认后恢复', lambda: approval(True), expected={'approved':True})
        case('取消后返回 False', lambda: approval(False), expected={'approved':False})
    elif identifier == 'rag':
        def rag():
            model = ReplyModel()
            result = module.ask_with_context(model, '几点关门？', ['周三九点关闭。', '周六开放。'])
            request = '\n'.join(str(m.content) for m in model.calls[0])
            require('九点' in request and '周六' in request and '几点关门' in request, '资料或问题没有发送给模型')
            require(isinstance(result, str), '需要返回回答文字')
        case('资料与问题一起进入模型', rag)
    elif identifier == 'retriever':
        class FixtureEmbeddings(Embeddings):
            def embed_documents(self, texts):
                return [[1., 0.] if '学习室' in text else [0., 1.] for text in texts]
            def embed_query(self, text):
                return [1., 0.]
        def retrieval():
            retriever = module.build_retriever(FixtureEmbeddings(), ['学习室九点关闭', '食堂供应早餐', '学习室周末开放'])
            documents = retriever.invoke('学习室')
            require(len(documents) == 2 and all('学习室' in d.page_content for d in documents), '没有取出两段相关资料')
        case('检索相关资料与数量限制', retrieval)
    elif identifier == 'mcp_tools':
        async def discover(fail=False):
            calls = []
            class Adapter:
                def __init__(self, target): calls.append(target)
                async def __aenter__(self): calls.append('enter'); return self
                async def list_tools(self):
                    if fail: raise ValueError('fixture')
                    return ['weather']
                async def __aexit__(self, *args): calls.append('exit')
            try:
                result = await module.discover_tools('fixture', Adapter)
                require(result == ['weather'], '没有返回工具列表')
            except ValueError:
                if not fail: raise
            require(calls == ['fixture', 'enter', 'exit'], '连接没有正确进入或关闭')
        case('发现工具并关闭连接', lambda: event_loop.run_until_complete(discover()),expected=['weather'])
        case('失败时也关闭连接', lambda: event_loop.run_until_complete(discover(True)))
    elif identifier == 'async_reply':
        async def asynchronous():
            called = []
            class Model:
                async def ainvoke(self, question):
                    called.append(question)
                    return AIMessage(content='异步回答')
            result = await module.reply_async(Model(), '问题')
            require(called == ['问题'] and result == '异步回答', '需要等待 ainvoke 再取出 content')
        case('异步调用确实被等待', lambda: event_loop.run_until_complete(asynchronous()),expected='异步回答')
    else:
        raise ValueError('未知入门任务')
    passed = sum(item['status'] == 'passed' for item in cases)
    return {'verdict': 'AC' if cases and passed == len(cases) else 'WA',
            'passed': passed, 'total': len(cases), 'cases': cases}


def live(identifier, payload, emit, make_model, config):
    module = importlib.import_module('practice.' + identifier)
    question = payload.get('question','你好')
    if identifier=='weather_tool':
        with patch.object(httpx,'get',wraps=httpx.get) as fetch:
            value=module.get_weather.invoke({'city':question.strip()})
        if not fetch.called:raise AssertionError('请按新版任务请求天气接口，运行结果不能来自预设天气字典。')
        emit({'type':'text','text':str(value)})
        return {'verdict':'OK','cases':[]}
    observed={'calls':0,'chunks':0}
    def observe(model):
        for name in ['invoke','stream','ainvoke']:
            original=getattr(model,name,None)
            if original is None:continue
            if name=='invoke':
                def invoke(*args,_original=original,**kwargs):
                    observed['calls']+=1
                    return _original(*args,**kwargs)
                object.__setattr__(model,name,invoke)
            elif name=='ainvoke':
                async def ainvoke(*args,_original=original,**kwargs):
                    observed['calls']+=1
                    return await _original(*args,**kwargs)
                object.__setattr__(model,name,ainvoke)
            else:
                def stream(*args,_original=original,**kwargs):
                    observed['calls']+=1
                    for chunk in _original(*args,**kwargs):
                        observed['chunks']+=1
                        yield chunk
                object.__setattr__(model,name,stream)
        return model
    model=observe(make_model(config)) if identifier!='first_reply' else None
    if identifier == 'first_reply':
        with patch.object(module, 'ChatOpenAI', side_effect=lambda **kwargs:observe(make_model(kwargs))):
            value = module.reply(config, question)
    elif identifier == 'stream_reply':
        value = module.stream_reply(model, question, lambda text: emit({'type': 'text', 'text': text}))
        if not observed['chunks']:raise AssertionError('请通过 model.stream 消费模型返回的片段。')
        return {'verdict': 'OK', 'cases': [], 'message': '流式回答已完成'}
    elif identifier == 'prompt_chain':
        value = module.make_chain(model).invoke({'topic': question})
    elif identifier == 'weather_agent':
        result = module.build_agent(model).invoke({'messages': [{'role': 'user', 'content': question}]})
        for message in result['messages']:
            if isinstance(message, ToolMessage):
                emit({'type': 'tool_end', 'name': message.name or 'get_weather', 'text': message.content})
        value = result['messages'][-1].content
    elif identifier == 'structured':
        result = module.extract_plan(model, question)
        value = result.model_dump_json(indent=2)
    elif identifier == 'rag':
        value = module.ask_with_context(model, question, ['学习室周三晚上九点关闭。'])
    elif identifier == 'conversation':
        history = [HumanMessage(content='我叫小林'), AIMessage(content='你好，小林。')]
        messages = module.chat(model, history, question)
        if not isinstance(messages, list) or not messages or not isinstance(messages[-1], AIMessage):
            raise TypeError('chat 需要返回包含本轮助手消息的消息列表。')
        value = messages[-1].content
    elif identifier == 'workflow':
        value = module.build_workflow(model).invoke({'question': question})['answer']
    elif identifier == 'checkpoint':
        app = module.build_chat(model, InMemorySaver())
        config = {'configurable': {'thread_id': payload.get('threadId') or 'main'}}
        app.invoke({'messages': [('user', '我叫小林。')]}, config)
        state = app.invoke({'messages': [('user', question)]}, config)
        value = state['messages'][-1].content
    elif identifier == 'async_reply':
        import asyncio
        value = asyncio.run(module.reply_async(model, question))
    else:
        raise ValueError('本节使用离线检查')
    if not observed['calls']:raise AssertionError('没有调用模型，请返回模型实际生成的内容。')
    emit({'type': 'text', 'text': str(value)})
    return {'verdict': 'OK', 'cases': [], 'message': '模型调用完成'}
