"""Typed preview inputs. Runtime results carry their own captured input values."""
def fields(*items):
    return [dict(name=name,type=kind,text=text) for name,kind,text in items]

MODEL=('model','ChatModel','<运行器创建的聊天模型>')
TOOLS=('tools','list[BaseTool]','[read, write, edit]')
CALLBACK=('on_event','Callable','<运行事件回调>')
CONFIG=('config','dict',"{'model': '<模型名称>', 'api_key': '••••', 'base_url': '<服务地址>'}")
PREVIEWS={
 'intro':[],
 'first_reply':fields(CONFIG,('question','str','你好，请介绍一下自己。')),
 'stream_reply':fields(MODEL,('question','str','你好，请介绍一下自己。'),('on_text','Callable','<逐段显示文本的回调>')),
 'prompt_chain':fields(MODEL,('topic','str','工具调用')),
 'weather_tool':fields(('city','str','杭州')),
 'weather_agent':fields(MODEL,('question','str','请查询杭州现在的天气。')),
 'structured':fields(MODEL,('text','str','我想去杭州玩三天。')),
 'conversation':fields(MODEL,('history','list[BaseMessage]',"[HumanMessage(content='我叫小林'), AIMessage(content='你好，小林。')]"),('question','str','我叫什么？')),
 'workflow':fields(MODEL,('question','str','你好，请介绍一下自己。')),
 'routing':fields(('state','dict',"{'need_tool': True}")),
 'checkpoint':fields(MODEL,('saver','InMemorySaver','<内存检查点保存器>'),('question','str','我叫什么？')),
 'approval':fields(('state','dict',"{'question': '确认修改 hello.py 吗？'}")),
 'rag':fields(MODEL,('question','str','学习室周三几点关门？'),('documents','list[str]',"['学习室周三晚上九点关闭。']")),
 'retriever':fields(('embeddings','Embeddings','<运行器提供的文本向量模型>'),('texts','list[str]',"['读取文件使用 read 工具。', '修改文件使用 edit 工具。']")),
 'async_reply':fields(MODEL,('question','str','你好，请介绍一下自己。')),
 'mcp_tools':fields(('target','str',"'https://example.invalid/mcp'"),('adapter_factory','Callable','<创建 MCP 连接的适配器工厂>')),
 'pi_model':fields(CONFIG),
 'pi_files':fields(('root','Path',"'workspace'"),('path','str',"'hello.py'"),('old','str',"'Hello'"),('new','str',"'你好'")),
 'pi_tools':fields(('message','AIMessage',"AIMessage(content='', tool_calls=[{'name': 'read', 'args': {'path': 'hello.py'}, 'id': 'call-1'}])"),TOOLS,CALLBACK),
 'pi_loop':fields(MODEL,TOOLS,('messages','list[BaseMessage]',"[HumanMessage(content='解释 hello.py')]"),('max_rounds','int','8')),
 'pi_context':fields(('messages','list[BaseMessage]',"[SystemMessage(content='先读文件'), HumanMessage(content='问题1'), AIMessage(content='回答1'), HumanMessage(content='问题2'), AIMessage(content='回答2')]"),('keep_turns','int','1')),
 'pi_session':fields(('leaf','str',"'c'"),('self.entries','list[dict]',"[{'id': 'a', 'parentId': None, 'message': <用户消息>}, {'id': 'c', 'parentId': 'a', 'message': <助手消息>}]")),
 'pi_graph':fields(MODEL,TOOLS,('checkpointer','InMemorySaver','<内存检查点保存器>')),
 'pi_skills':fields(('root','Path',"'workspace/skills'")),
 'pi_events':fields(('text','str',repr('{"type":"text","text":"你好"}\n'))),
 'pi_limits':fields(('self.calls','int','0'),('self.tokens','int','0'),('self.max_calls','int','1'),('self.max_tokens','int','20000')),
 'pi_evaluate':fields(('events','list[dict]',"[{'type': 'tool_end', 'name': 'read', 'status': 'success'}, {'type': 'model_end'}]"),('required_tools','list[str]',"['read']"),('expected_files','dict',"{'hello.py': 'print(1)'}"),('actual_files','dict',"{'hello.py': 'print(1)'}")),
 'project':fields(('root','Path',"'workspace'"),('data','Path',"'.mini-pi'"),MODEL,CALLBACK,('question','str','请阅读 hello.py，把问候语改成中文，并运行检查。')),
}
LIVE_INPUT={'prompt_chain':'topic','structured':'text','weather_tool':'city'}
RUNTIME_OUTPUT={
 'first_reply':'str：模型生成的完整回答文本。',
 'stream_reply':'str：按接收顺序拼接的完整回答文本。',
 'prompt_chain':'str：围绕 topic 生成的解释文本。',
 'weather_tool':'str：城市：天气状况，温度℃。使用本次天气接口返回的数据。',
 'weather_agent':'str：模型依据天气工具实际返回的数据生成回答。',
 'structured':'TravelPlan：包含 city 字符串与 days 整数。',
 'conversation':'str：模型结合已有 history 与本次 question 生成的回答。',
 'workflow':'str：流程清理问题后由模型生成的回答。',
 'checkpoint':'str：模型根据同一线程中保存的上一轮消息回答当前问题。',
 'rag':'str：模型根据 documents 中的资料回答 question。',
 'async_reply':'str：异步调用完成后取得的模型回答。',
 'project':'Agent 运行后的回答，工具调用过程可在下方展开查看。',
}
