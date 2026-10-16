"""Usage examples for imported components and supplied helpers in each lesson."""
from textwrap import dedent

NOTES = {
'intro': '''
### 观察函数的输入和输出

`def demo():` 定义一个不接收参数的函数，调用 `demo()` 才开始执行函数体。`print(value)` 把值显示到运行区，函数执行到末尾且没有 `return` 时，返回值是 `None`。这一节通过打印观察流程，后面的任务会用返回值把数据交给其他组件。

```python
def show_result():
    print("工具返回：23℃")

value = show_result()
print(value)  # None
```
''',
'first_reply': '''
### 客户端对象与返回消息

`from langchain_openai import ChatOpenAI` 从模型集成包中导入客户端类。`ChatOpenAI(...)` 创建对象，`client.invoke(question)` 发出一次请求并等待回答，返回消息的 `content` 在本节的纯文本任务中是字符串。创建对象与发出请求是两个步骤，可以重复使用同一个客户端。

```python
from langchain_openai import ChatOpenAI

# config 由运行器根据读者填写的 .env 提供。
client = ChatOpenAI(
    model=config["model"],
    api_key=config["api_key"],
    base_url=config["base_url"],
)
answer = client.invoke("请解释什么是工具调用。")
print(answer.content)  # 模型生成的回答文字
```

本页后面还会用到 `ChatAnthropic` 和 `ChatOllama`。它们分别来自 `langchain_anthropic` 和 `langchain_ollama`，也先创建模型对象，再通过 `invoke()` 取得回答，构造参数则按各自服务填写。
''',
'stream_reply': '''
### 读取流式消息片段

`model.stream(question)` 返回可以遍历的片段序列，每次得到的片段通常是 `AIMessageChunk`，其中 `content` 保存这一次新增的文字。片段可能为空，也可能包含多个字，因此需要按到达顺序保存。本任务只处理纯文本片段。

```python
from langchain_core.messages import AIMessageChunk

chunks = [
    AIMessageChunk(content="你"),
    AIMessageChunk(content=""),
    AIMessageChunk(content="好"),
]
parts = [chunk.content for chunk in chunks if chunk.content]
print("".join(parts))  # 你好
```

`on_text` 是调用方传入的显示函数，`on_text(piece)` 会立即显示一段文字。把这个函数作为参数传递时写 `on_text`，拿到片段后才用括号调用它，最终还要返回所有片段拼成的字符串。
''',
'prompt_chain': '''
### 先生成消息，再解析回答

`ChatPromptTemplate` 来自 `langchain_core.prompts`，用 `from_messages()` 创建提示模板。列表中的每项是角色和文字组成的二元组，`system` 放回答要求，`human` 放用户输入，`{topic}` 是每次调用时填写的变量。

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "用生活中的例子解释概念。"),
    ("human", "请解释：{topic}"),
])
value = prompt.invoke({"topic": "工具调用"})
messages = value.to_messages()
print(messages[-1].content)  # 请解释：工具调用
```

`StrOutputParser` 来自 `langchain_core.output_parsers`，负责把模型返回的消息转成字符串。下面用手工创建的 `AIMessage` 演示解析过程，实际运行时这条消息由模型生成。

```python
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
text = parser.invoke(AIMessage(content="工具让程序执行具体操作。"))
print(text)  # 工具让程序执行具体操作。
```

`prompt | model | parser` 按顺序连接三个组件，前一个组件的结果会成为后一个组件的输入。整条链接收 topic 字典，最后返回字符串。
''',
'weather_tool': '''
### 把函数包装成工具

`tool` 从 `langchain_core.tools` 导入，写在函数上方的 `@tool` 会读取函数名、参数类型和三引号说明，生成模型能够理解的工具描述。包装后的对象有 `name`、`description` 和 `args` 字段，运行时用 `invoke()` 传入参数字典。

```python
from langchain_core.tools import tool

@tool
def double(number: int) -> int:
    """将一个整数乘以二。"""
    return number * 2

print(double.name)  # double
print(double.invoke({"number": 3}))  # 6
```

这里的 `number: int` 用于描述和检查工具参数，返回值来自原函数的 `return`。天气工具也按同样方式接收 city，再请求真实天气服务。

### 发出 HTTP 请求并解析响应

`httpx` 用于发送网络请求。`httpx.get(url, params=..., headers=..., timeout=10)` 发出 GET 请求，params 是查询参数，headers 是请求头，timeout 限制等待时间。返回的 Response 提供 `raise_for_status()` 检查 HTTP 状态，`json()` 将响应正文解析为字典。

```python
import httpx

def request_weather(config, code):
    response = httpx.get(
        config["url"],
        params={"areacode": code},
        headers={"X-APISpace-Token": config["api_key"]},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
```

天气凭证属于访问服务的认证信息，放在请求头中读取，工具参数仍然只有 city。下面会用已经给出的城市编码与配置辅助函数准备 code 和 config，再读取响应中的天气字段。
''',
'weather_agent': '''
### 创建 Agent 并读取它的状态

`create_agent` 从 `langchain.agents` 导入，`model` 接收已创建的聊天模型，`tools` 接收工具对象列表，`system_prompt` 是模型每轮需要遵守的回答要求。返回的 Agent 提供 `invoke()`，其输入和输出都使用状态字典。

`get_weather` 从 `practice.weather_tool` 导入，它就是上一节创建的工具对象。可以先通过 `.invoke({"city": ...})` 单独确认工具结果，再把对象交给 Agent。

```python
from langchain.agents import create_agent
from practice.weather_tool import get_weather

print(get_weather.invoke({"city": "杭州"}))
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="查询实时天气时使用工具，依据结果回答，失败时明确说明。",
)
state = agent.invoke({
    "messages": [{"role": "user", "content": "杭州天气怎么样？"}],
})
print(state["messages"][-1].content)
```

`messages` 保存这次执行中的消息，`role` 标记用户等角色，`content` 保存文字。返回列表可能还包含工具请求和结果，所以用 `[-1]` 读取最后一条助手回答，读取中间消息时需要留意它的角色。
''',
'structured': '''
### 声明字段与创建数据对象

`BaseModel` 和 `Field` 从 `pydantic` 导入。继承 `BaseModel` 的类描述一组有名字和类型的数据字段，`Field(description=...)` 补充字段用途，`description` 本身不会给字段提供默认值。

```python
from pydantic import BaseModel, Field

class TravelPlan(BaseModel):
    city: str = Field(description="目的地城市")
    days: int = Field(description="旅行天数")

plan = TravelPlan(city="杭州", days=3)
print(plan.city)  # 杭州
print(plan.days)  # 3
print(plan.model_dump())  # {'city': '杭州', 'days': 3}
```

这里先手工创建对象，便于观察字段。任务中的 `model.with_structured_output(TravelPlan, method="function_calling")` 会返回一个新的调用对象，再用它的 `invoke(text)` 让模型根据用户需求填写这些字段。传入的是 `TravelPlan` 这个类，得到的结果才是带具体值的实例。
''',
'conversation': '''
### 创建和读取消息对象

`langchain_core.messages` 提供不同角色的消息类。`HumanMessage` 表示用户输入，`AIMessage` 表示助手回答，构造时通过 `content` 填入正文，创建后通过 `.content` 读取文字，通过 `.type` 读取消息类型。

```python
from langchain_core.messages import HumanMessage, AIMessage

question = HumanMessage(content="我叫小林。")
answer = AIMessage(content="你好，小林。")
print(question.content)  # 我叫小林。
print(question.type)  # human
print(answer.content)  # 你好，小林。
print(answer.type)  # ai
history = [question, answer]
```

`HumanMessage(content=question)` 中，左边的 content 是类的参数名，右边的 question 是你要发送的字符串变量。将消息列表传给 `model.invoke(messages)` 后，模型会返回一条新的 `AIMessage`，需要把整条消息追加到历史，后续轮次才能保留角色等信息。

下面演示模型如何收到新一轮问题，`model` 使用之前创建的聊天模型对象。

```python
messages = [*history, HumanMessage(content="我叫什么？")]
reply = model.invoke(messages)
new_history = [*messages, reply]
print(new_history[-1].content)
```
''',
'workflow': '''
### 声明状态并连接节点

`TypedDict` 从 `typing_extensions` 导入，用类的形式标明字典字段及其类型，实际传入的 state 仍是普通字典。`StateGraph`、`START`、`END` 来自 `langgraph.graph`，分别用于创建图、指定入口和指定结束位置。

`add_node(name, function)` 注册节点，`add_edge(from_name, to_name)` 连线，`compile()` 生成可执行的图，随后用 `invoke(initial_state)` 开始执行。

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str

def clean(state):
    return {"question": state["question"].strip()}

graph = StateGraph(State)
graph.add_node("clean", clean)
graph.add_edge(START, "clean")
graph.add_edge("clean", END)
app = graph.compile()
print(app.invoke({"question": "  你好  "}))
# {'question': '你好'}
```

节点返回的字典用于更新状态中的对应字段，因此 clean 可以只返回处理后的 question，后续节点再从更新后的状态读取它。
''',
'routing': '''
### 条件边如何使用返回值

`add_conditional_edges(source, router)` 接收起点节点名和路由函数。执行完 source 后，图会把当前状态传给 router，然后根据它返回的节点名选择下一步。下面假设 decide、tools 和 answer 已经通过 `add_node()` 注册。

```python
def choose_next(state):
    return "tools" if state["need_tool"] else "answer"

graph.add_conditional_edges("decide", choose_next)
print(choose_next({"need_tool": True}))  # tools
print(choose_next({"need_tool": False}))  # answer
```

这里传入 `choose_next` 函数对象，让图在运行时调用它。`choose_next(state)` 的返回值是字符串，必须与已注册的节点名称对应，路由函数内部不用执行节点代码。
''',
'checkpoint': '''
### 消息状态与线程配置

`MessagesState` 从 `langgraph.graph` 导入，已经定义 messages 字段及其合并方式。新消息会按消息 ID 合并到旧列表，同 ID 的消息可以更新原记录，所以节点返回新增消息时，旧对话不会被整批替换。

`InMemorySaver` 从 `langgraph.checkpoint.memory` 导入，用 `InMemorySaver()` 创建内存检查点保存器，再交给 `compile(checkpointer=saver)`。`StateGraph`、`START` 和 `END` 延续上一节的节点连接方式。

```python
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

def answer(state):
    return {"messages": [AIMessage(content="收到") ]}

graph = StateGraph(MessagesState)
graph.add_node("answer", answer)
graph.add_edge(START, "answer")
graph.add_edge("answer", END)
app = graph.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "demo"}}
first = app.invoke({"messages": [("user", "你好")]}, config)
second = app.invoke({"messages": [("user", "再问一次")]}, config)
print(len(first["messages"]))  # 2
print(len(second["messages"]))  # 4
```

示例手工创建 AIMessage 来观察历史变化，没有请求模型。真实任务的节点会调用模型，`configurable` 是图的运行配置字典，其中的 `thread_id` 用来找到同一个线程的状态。
''',
'approval': '''
### 暂停请求与恢复命令

`interrupt` 和 `Command` 从 `langgraph.types` 导入。`interrupt(payload)` 把确认内容交给图的调用方并暂停，payload 可以是包含问题和操作信息的字典。调用方随后把 `Command(resume=value)` 交给同一个图，节点重新执行到 interrupt 时会取得这个 value。

```python
from langgraph.types import interrupt, Command

def approve(state):
    decision = interrupt({"question": state["question"]})
    return {"approved": decision is True}

# app 是运行器搭建的、带检查点的图，包含上面的节点。
config = {"configurable": {"thread_id": "edit-demo"}}
paused = app.invoke({"question": "确认修改文件吗？"}, config)
print(paused["__interrupt__"][0].value)
# {'question': '确认修改文件吗？'}
finished = app.invoke(Command(resume=True), config)
print(finished["approved"])  # True
```

恢复时保留相同的 thread_id，图才能找到暂停记录。`decision is True` 只接受布尔值 True，字符串 `"True"` 和数字 1 都不会被当作同意。不要在调用 interrupt 之前执行修改，因为恢复会从节点开头重新运行。
''',
'rag': '''
### 用不同角色放置要求和资料

`SystemMessage` 和 `HumanMessage` 从 `langchain_core.messages` 导入。两者都用 `content` 接收文字，但 SystemMessage 用来说明回答要求，HumanMessage 用来传递这次的问题和资料。创建消息只是在组织数据，调用模型时才会发送这些数据。

```python
from langchain_core.messages import SystemMessage, HumanMessage

rules = SystemMessage(content="请只根据资料回答。")
request = HumanMessage(content="资料：周三九点关闭。\\n问题：几点关闭？")
messages = [rules, request]
print(messages[0].type)  # system
print(messages[1].content)
# 资料：周三九点关闭。
# 问题：几点关闭？
```

资料列表可以通过 `"\\n".join(documents)` 用换行连接，放入 HumanMessage 后与问题一起发送。把外部资料放进消息正文，能够让模型在这一轮请求中读取它，资料仍需要按数据来理解。
''',
'retriever': '''
### 建立索引与读取 Document

`InMemoryVectorStore` 从 `langchain_core.vectorstores` 导入，它在当前进程中保存文本及其向量。`from_texts(texts, embedding=embeddings)` 接收字符串列表和向量模型，返回向量库对象，`as_retriever(search_kwargs={"k": 2})` 再把它包装成检索器。

```python
from langchain_core.vectorstores import InMemoryVectorStore

# embeddings 是任务运行器传入的向量模型。
texts = ["读取文件使用 read 工具。", "修改文件使用 edit 工具。"]
store = InMemoryVectorStore.from_texts(texts, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 2})
documents = retriever.invoke("怎样读取文件？")
for document in documents:
    print(document.page_content)
```

`search_kwargs` 是检索参数字典，k 指定返回数量上限。每个结果是 Document，`page_content` 保存正文，`metadata` 保存来源等附加信息，返回对象本身不同于直接返回文本。任务中的 embeddings 已经提供，不需要在函数内部再创建付费服务客户端。
''',
'async_reply': '''
### 协程对象与等待结果

调用 `async def` 定义的函数时，先得到一个协程对象，使用 await 后才取得结果。`model.ainvoke(question)` 是模型的异步完整回答接口，返回消息对象，本任务再取出它的 content。

```python
import asyncio

async def add(a, b):
    return a + b

async def main():
    result = await add(2, 3)
    print(result)  # 5

# 在普通 Python 脚本中执行下面这行。
asyncio.run(main())
```

`asyncio` 是 Python 自带的异步库，`asyncio.run(coroutine)` 创建事件循环并等待协程结束。网页运行器已经有事件循环，所以你的 reply_async 内只需要 await，避免在它内部再次调用 asyncio.run。异步流式接口 `astream()` 返回异步迭代器，需要使用 async for 逐段读取。
''',
'mcp_tools': '''
### 适配器对象与连接范围

`MCPAdapter` 从 `langchain.mcp` 导入，构造时接收服务目标，进入 `async with` 后可以调用 `await adapter.list_tools()` 取得工具列表。实际执行服务工具时，需要让 Agent 的运行保持在有效的连接上下文中，下面先观察工具发现的写法。

```python
from langchain.mcp import MCPAdapter

async def inspect_tools(target):
    async with MCPAdapter(target) as adapter:
        tools = await adapter.list_tools()
        print([item.name for item in tools])
        return tools
```

`target` 可以是服务地址。课程任务将创建连接的动作作为 adapter_factory 参数传入，因此要调用 `adapter_factory(target)`，这样既能连接实际服务，也能在提交时换成本地适配器验证行为。`async with` 负责进入和退出连接，工具发现发生异常时也会执行退出清理。

后面的组合示例还从 langchain.agents 导入 create_agent，将发现的 tools 传给它，再通过 `await agent.ainvoke(...)` 处理用户问题。这个调用放在 async with 内，完成以后才退出连接。本节的小任务只验证工具发现与连接退出，不要求调用服务执行工具。
''',
'pi_model': '''
### 配置文件怎样变成模型参数

`Path` 从 Python 标准库 `pathlib` 导入，`Path(".env")` 表示一个路径对象。`dotenv_values` 从 `dotenv` 导入，读取文件后返回键值映射，`interpolate=False` 表示不展开文件值中的变量表达式，`dict(...)` 将结果转成普通字典。这一步读取配置，不会把密钥打印到页面。

```python
from pathlib import Path
from dotenv import dotenv_values

# .env 中的字段由读者自己填写，不要打印完整配置。
values = dict(dotenv_values(Path(".env"), interpolate=False))
model_name = values.get("MODEL_NAME")
```

已有的 load_config 会将配置整理成 model、api_key 和 base_url。`ChatOpenAI` 从 `langchain_openai` 导入，接收这些值后返回模型客户端，只有后续调用 invoke 或 stream 才会请求模型。这里还需要设置超时、重试和兼容选项，下面的本节说明会分别介绍它们。

```python
from langchain_openai import ChatOpenAI

client = ChatOpenAI(
    model=config["model"],
    api_key=config["api_key"],
    base_url=config["base_url"],
    timeout=30,
    max_retries=2,
    use_responses_api=False,
    stream_usage=False,
)
```
''',
'pi_files': '''
### 路径对象与文本读写

`Path` 从 Python 标准库 `pathlib` 导入，使用 `/` 拼接目录和文件名，`read_text(encoding="utf-8")` 读取文本，`write_text(text, encoding="utf-8")` 写入文本。文件路径和文件内容是两种不同的数据。

```python
from pathlib import Path

root = Path("workspace")
root.mkdir(parents=True, exist_ok=True)
target = root / "example.txt"
target.write_text("Hello", encoding="utf-8")
print(target.read_text(encoding="utf-8"))  # Hello
```

`mkdir(parents=True, exist_ok=True)` 会建立缺少的父目录，目录已存在时继续执行。本文件的 workspace_path 已经用 resolve 和 is_relative_to 检查目录范围，任务里优先复用给定的 read_file 和 write_file，让编辑操作沿用这些检查。
''',
'pi_tools': '''
### 把一次请求对应到一次工具结果

`tool` 从 `langchain_core.tools` 导入，用 @tool 把函数包装成工具对象。`ToolMessage` 从 `langchain_core.messages` 导入，用 content 保存结果，用 tool_call_id 指明它回答的是哪次工具请求，status 可以是 success 或 error。

```python
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

@tool
def echo(text: str) -> str:
    """原样返回传入的文字。"""
    return text

call = {"name": "echo", "args": {"text": "你好"}, "id": "call-1"}
value = echo.invoke(call["args"])
reply = ToolMessage(content=value, tool_call_id=call["id"])
print(reply.content)  # 你好
print(reply.tool_call_id)  # call-1
```

本文件还导入 `mini_pi.files` 中的 read_file、write_file 和 edit_file，分别读取、完整写入和替换文件内容。`mini_pi.diffs.preview_edit` 的 preview_edit 返回修改前后内容和 patch 差异文本，已有的 edit 工具会把预览中的 patch 一起交回。`mini_pi.limits.truncate_output` 的 truncate_output 接收文本与长度上限，超长时截取并补充提示，避免工具结果过大。

```python
from mini_pi.files import read_file, write_file, edit_file
from mini_pi.diffs import preview_edit
from mini_pi.limits import truncate_output

write_file(root, "example.txt", "Hello")
print(read_file(root, "example.txt"))  # Hello
preview = preview_edit(root, "example.txt", "Hello", "你好")
edit_file(root, "example.txt", "Hello", "你好")
short_result = truncate_output(preview["patch"], limit=200)
```

这些文件工具的包装已经给出，execute_calls 负责根据名称找到工具，执行后生成配对的 ToolMessage，再通过 on_event 通知界面开始与结束状态。
''',
'pi_loop': '''
### 模型绑定工具与执行工具的区别

`model.bind_tools(tools)` 返回带工具描述的模型对象，让模型能够产生 tool_calls。它只告诉模型有哪些工具，真正的 Python 函数由程序执行。`execute_calls` 从你之前完成的 `mini_pi.tools` 导入，接收助手消息与工具列表，返回 ToolMessage 列表。

```python
from mini_pi.tools import execute_calls

bound = model.bind_tools(tools)
answer = bound.invoke(messages)
print(answer.tool_calls)
if answer.tool_calls:
    results = execute_calls(answer, tools)
    messages = [*messages, answer, *results]
```

tool_calls 的每项包含 name、args 和 id，空列表表示模型这次没有请求工具。把助手请求和工具结果都放回历史后，再次调用 bound.invoke，模型才能读取执行结果。完整循环需要重复这个步骤，直到没有工具请求或达到调用上限。
''',
'pi_context': '''
### 识别角色并保留完整轮次

`SystemMessage` 和 `HumanMessage` 从 `langchain_core.messages` 导入，用 isinstance 可以判断一个消息对象的角色。系统说明独立保存，每遇到一条用户消息就开始新一轮，后面的助手回答和工具结果属于这轮。

```python
from langchain_core.messages import SystemMessage, HumanMessage

rules = SystemMessage(content="先读文件，再回答。")
question = HumanMessage(content="hello.py 有什么作用？")
print(isinstance(rules, SystemMessage))  # True
print(isinstance(question, HumanMessage))  # True
```

`text_of` 从项目的 `mini_pi.streaming` 导入，接收消息并提取纯文本。content 是字符串时直接返回，content 是内容块列表时只拼接 type 为 text 的块。已有的摘要辅助函数会用它整理旧历史。

```python
from mini_pi.streaming import text_of

print(text_of(question))  # hello.py 有什么作用？
system, turns = split_turns([rules, question])
print(len(system))  # 1
print(len(turns))  # 1
```

任务需要完成窗口选择，split_turns 和摘要函数已经提供，理解这些辅助函数后可以保留消息对象本身，避免只保留文字而丢掉角色或工具调用 ID。
''',
'pi_session': '''
### 将消息写入 JSON，再恢复为对象

`message_to_dict` 和 `messages_from_dict` 从 `langchain_core.messages` 导入。前者把一条消息转换成普通字典，后者接收字典列表并恢复消息对象，角色、正文和工具字段可以随记录保存。下面用同一模块中的 HumanMessage 创建用户消息，再观察保存和恢复的过程。

```python
import json
from langchain_core.messages import (
    HumanMessage,
    message_to_dict,
    messages_from_dict,
)

message = HumanMessage(content="请解释 hello.py")
record = message_to_dict(message)
line = json.dumps(record, ensure_ascii=False)
restored = messages_from_dict([json.loads(line)])
print(restored[0].content)  # 请解释 hello.py
```

`json` 是 Python 自带的 JSON 编解码模块，dumps 把字典转成字符串，loads 把字符串恢复为字典。`uuid` 提供 uuid4，调用 `.hex` 取得随机记录 ID，`Path` 来自 pathlib，用来保存会话文件路径，`open("a")` 以追加方式写入新行。

```python
import uuid
from pathlib import Path

entry_id = uuid.uuid4().hex
path = Path("session.jsonl")
# append() 已经负责创建目录和写文件，branch() 只读取 self.entries。
```

保存的记录字段是 id、parentId 和 message，parentId 为 None 表示根节点。branch 需要先沿父节点恢复顺序，再把消息字典列表交给 messages_from_dict。
''',
'pi_graph': '''
### 消息合并规则与已有辅助函数

`Annotated` 从 typing 导入，给字段附加框架需要的合并规则，`TypedDict` 从 typing_extensions 导入，用来描述状态字典。`add_messages` 从 `langgraph.graph.message` 导入，按消息 ID 合并新旧消息，相同 ID 可以替换原消息，不同 ID 则追加。示例用 HumanMessage 创建用户消息，这次还通过 id 指定消息标识，以观察更新行为。

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

old = [HumanMessage(content="原问题", id="user-1")]
new = [HumanMessage(content="修正后的问题", id="user-1")]
merged = add_messages(old, new)
print(len(merged))  # 1
print(merged[0].content)  # 修正后的问题
```

`StateGraph`、`START`、`END` 仍从 langgraph.graph 导入。下面只演示如何注册节点、连接入口和结束并编译，实际任务已经给出了 model 和 tools 两个节点，需要补上条件边和返回边。

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("keep", lambda state: {})
graph.add_edge(START, "keep")
graph.add_edge("keep", END)
app = graph.compile()
```

已有节点会组合前面写过的函数。`window_context` 来自 mini_pi.context，保留近期完整轮次。`collect_stream` 来自 mini_pi.streaming，把流式片段聚合成完整助手消息并调用显示回调。`execute_calls` 来自 mini_pi.tools，执行工具并返回工具消息。`Budget` 来自 mini_pi.limits，在 before_call 时检查上限，再由 record 累计 token。`ToolMessage` 来自 langchain_core.messages，用于把用户拒绝执行的结果配对到原工具请求。

```python
from mini_pi.context import window_context
from mini_pi.streaming import collect_stream
from mini_pi.tools import execute_calls
from mini_pi.limits import Budget
from langchain_core.messages import ToolMessage

budget = Budget(max_calls=8, max_tokens=20000)
budget.before_call()
request = window_context(messages)
answer = collect_stream(bound.stream(request), on_text)
budget.record(answer.usage_metadata or {})
results = execute_calls(answer, tools, on_event)
refused = ToolMessage(
    content="用户取消了修改。",
    tool_call_id="call-1",
    status="error",
)
```

这里的 messages、bound、tools 和回调都由已有节点提供。理解它们的数据流后，本节只需要连接节点，不用重写模型请求、流式处理或预算组件。
''',
'pi_skills': '''
### 遍历技能文件并包装加载工具

`Path` 从 pathlib 导入，`Path(root).glob("*/SKILL.md")` 查找 root 下每个一级子目录中的技能文件。路径的 parent.name 是技能目录名，read_text 读取全文，已有的 discover_skills 会把名称、描述和路径整理成字典。

```python
from pathlib import Path

for path in sorted(Path("workspace/skills").glob("*/SKILL.md")):
    print(path.parent.name)
    text = path.read_text(encoding="utf-8")
```

`tool` 从 langchain_core.tools 导入，在内部函数上使用 @tool，返回的对象才能交给模型。技能工具接收名称并返回说明文本，下面先用一个简化目录演示包装方式。

```python
from langchain_core.tools import tool

catalog = {"review": "先读代码，再检查边界输入。"}

@tool
def load_skill(name: str) -> str:
    """按名称读取技能说明。"""
    return catalog[name]

print(load_skill.invoke({"name": "review"}))
```

实际任务把示例中的字符串目录换成 discover_skills 返回的文件目录，再从对应 path 读取文本。返回 load_skill 工具对象即可，让 Agent 在需要时调用它。
''',
'pi_events': '''
### JSON 文本与字典的相互转换

`json` 是 Python 自带的模块，`json.dumps(value, ensure_ascii=False)` 将字典编码成 JSON 字符串，`json.loads(text)` 解析一段完整 JSON 并返回 Python 对象。ensure_ascii=False 可以让中文保持可读。

```python
import json

event = {"type": "text", "text": "你好"}
line = json.dumps(event, ensure_ascii=False) + "\\n"
restored = json.loads(line)
print(restored["type"])  # text
print(restored["text"])  # 你好
```

loads 可以解析完整事件，也可能解析出列表或数字，因此还要检查结果是 dict 且 type 是字符串。`pending.split("\\n", 1)` 将第一行与剩余部分分开，只有找到完整换行后才交给 loads，末尾的半行继续留在 pending。
''',
'pi_limits': '''
### 实例字段与预算累计

`Budget(...)` 创建保存运行计数的实例，`self.calls` 和 `self.tokens` 分别是已经尝试的模型次数和累计 token，`self.max_calls` 与 `self.max_tokens` 是上限。before_call 在请求前执行，record 在取得模型用量后执行。

```python
budget = Budget(max_calls=2, max_tokens=100)
budget.before_call()
budget.record({"total_tokens": 30})
print(budget.calls)  # 1
print(budget.tokens)  # 30
```

本文件导入 `mini_pi.streaming` 中的 text_of，用在已有的 estimate_tokens 中，把消息文字取出来后估计长度。下面使用 HumanMessage 创建一条用户消息，观察提取正文和估计长度的结果。`usage_metadata` 是模型消息中的用量字典，也可能为 None，所以调用 record 时使用 `answer.usage_metadata or {}`。

```python
from mini_pi.streaming import text_of
from langchain_core.messages import HumanMessage

message = HumanMessage(content="你好")
print(text_of(message))  # 你好
print(estimate_tokens([message]))  # 2
```

本任务只补全 before_call，其他函数已经实现。达到任意上限时应先拒绝调用，避免拒绝后仍增加 calls。
''',
'pi_evaluate': '''
### 从事件列表计算报告字段

本任务使用 Python 的列表、字典、all 和 sum，不需要导入外部包。字典的 `get(key, default)` 在键缺失时返回默认值，`all(...)` 判断所有条件是否满足，`sum(...)` 可以统计布尔条件为真的次数。

```python
events = [
    {"type": "tool_end", "name": "read", "status": "success"},
    {"type": "model_end"},
]
completed = [
    event.get("name") for event in events
    if event.get("type") == "tool_end"
    and event.get("status") == "success"
]
print(all(name in completed for name in ["read"]))  # True
print(sum(event.get("type") == "model_end" for event in events))  # 1
```

工具名称列表用于核对过程，expected_files 与 actual_files 用于核对文件内容。只有两项都满足时 passed 才为 True，返回字段仍按任务页的接口说明组织。
''',
'project': '''
### 装配对象并连接事件回调

`MiniPi` 从 `mini_pi.app` 导入，构造函数接收工作目录 root、数据目录 data 和可选模型 model，返回能够执行 run 和 close 的 Agent 对象。on_event 是接收事件字典的函数，approve=True 让修改操作先等待确认，context_mode="window" 使用窗口上下文。

`EventDecoder` 和 `encode_event` 从 `mini_pi.events` 导入。encode_event 将字典编码成带换行的 JSON，EventDecoder.feed 再恢复完整事件列表。已经提供的 display 负责把它们接到界面回调。

```python
from mini_pi.events import EventDecoder, encode_event

decoder = EventDecoder()
line = encode_event({"type": "text", "text": "你好"})
restored = decoder.feed(line)
print(restored[0]["text"])  # 你好
```

下面的 on_event 用 print 示范如何接收事件，真实网页会传入显示函数。构建完成后由调用方运行任务，结束时始终调用 close 释放数据库等资源。

```python
from mini_pi.app import MiniPi

def on_event(event):
    print(event["type"])

agent = MiniPi(
    root="workspace",
    data=".mini-pi",
    model=model,
    on_event=on_event,
    approve=True,
    context_mode="window",
)
try:
    agent.run("请阅读 hello.py 并解释它。")
finally:
    agent.close()
```
''',
}


def enrich(identifier, lesson):
    note = dedent(NOTES[identifier]).strip()
    first, separator, rest = lesson.strip().partition("\n\n")
    return first + "\n\n" + note + ("\n\n" + rest if separator else "")
