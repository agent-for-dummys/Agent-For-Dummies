"""Small, independent lessons before the Pi reconstruction tasks."""
from textwrap import dedent

LESSONS = []


def lesson(id, group, title, code, lesson_text, task, starter, success,
           hints, live=False, question="你好，请介绍一下自己。"):
    LESSONS.append({
        "id": id, "group": group, "title": title,
        "file": f"practice/{id}.py", "phase": "foundation",
        "mode": "model" if live else "deterministic", "live": live,
        "example": dedent(code).strip() + "\n",
        "starter": dedent(starter).strip() + "\n",
        "lesson": dedent(lesson_text).strip(), "task": task,
        "success": success, "hints": hints, "question": question,
    })


lesson("intro", "认识 Agent", "从聊天走向行动", '''
def demo():
    print("用户：杭州的天气怎么样？")
    print("模型选择工具：get_weather(city='杭州')")
    weather = {"city": "杭州", "temperature": 23}
    print("工具返回：", weather)
    print("模型回答：杭州的示例温度是 23℃。")
''', '''
你可以先把大模型理解成一个能够接收文字、生成回答的程序。当你让它解释一个概念时，一次对话通常就够了，但如果你问“杭州现在多少度”，它需要先取得天气数据，才能给出可靠的回答。

Agent 就是在模型周围加上能够行动的程序。模型提出“查询杭州天气”，程序执行查询，再把结果交给模型组织成回答。这个过程可以重复多次，直到任务完成。

规划帮助 Agent 拆分目标，记忆保留需要继续使用的信息，工具让程序读取文件、查询数据或执行操作。简单的 Agent 可以先只有一个模型和一个工具，其他能力随后逐步加入。

```text
用户的问题
    ↓
模型：需要调用工具吗？
    ↓ 是
程序执行工具 → 把结果交回模型
    ↓
模型给出回答
```

**LangChain** 提供模型、消息、提示模板和工具等组件，**LangGraph** 帮助我们安排步骤、保存状态并控制循环。**ReAct** 是让模型根据行动结果决定下一步的思路，**RAG** 是先查找资料、再根据资料回答的方法，这些概念会分别出现在模型调用、工具执行、流程控制和资料问答的例子中。

右侧是一段不联网的流程演示，天气数字是教学数据。点击运行，先观察“模型选择工具”和“程序执行工具”这两个不同动作。接下来的小任务会把这个演示逐渐换成真正的模型调用，最后再组合成能够读写代码的 mini-pi。
''', "运行右侧演示，找到工具返回的数据，再用右上角箭头进入第一项编程任务。", '''
def demo():
    print("用户：杭州的天气怎么样？")
    print("模型选择工具：get_weather(city='杭州')")
    weather = {"city": "杭州", "temperature": 23}
    print("工具返回：", weather)
    print("模型回答：杭州的示例温度是 23℃。")
''', "看到问题、工具选择、工具结果和最终回答依次出现，就可以开始下一节了。", [])

lesson("first_reply", "认识 Agent", "让大模型回答第一个问题", '''
from langchain_openai import ChatOpenAI


def reply(config, question):
    model = ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    answer = model.invoke(question)
    return answer.content
''', '''
调用大模型 API 时，Python 程序会把问题发送到模型服务，等待服务生成回答后，再把返回内容显示出来。下面的 reply 函数会完整地完成这个过程，其中 config 提供连接信息，question 保存用户输入的问题。

先打开代码区左上角的文件按钮，选择 `.env`，填写自己的 `MODEL_API_KEY`、`MODEL_NAME` 和 `MODEL_BASE_URL`。网站会把这些字段读成 `config` 字典，运行时传入你编写的函数。型号必须是自己账号能够调用的型号。

`ChatOpenAI` 是 LangChain 提供的聊天模型类，可以把它理解成连接模型服务的客户端。创建以后得到一个 model 对象，相当于拿到了一个可以重复发送问题的入口，调用 `invoke()` 时才会真正发送请求。

```python
from langchain_openai import ChatOpenAI

def reply(config, question):
    model = ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    answer = model.invoke(question)
    return answer.content
```

括号里的 `model` 参数选择型号，`api_key` 是访问凭证，`base_url` 是服务地址，等号左边的 model 则是保存下来的客户端对象。`invoke()` 接收问题并等待完整回答，返回一条 `AIMessage` 消息，`.content` 取出它的内容。后续小任务会直接把这个模型对象作为参数传给你，便于专心学习新的组件。

### 换一个模型怎么调用

支持 OpenAI 兼容接口的服务可以继续使用 `ChatOpenAI`，只更换连接配置。例如 OpenAI 使用 `https://api.openai.com/v1`，智谱的兼容入口使用 `https://open.bigmodel.cn/api/paas/v4/`，其他兼容服务填写它们自己的地址和型号。

原生协议不同的模型需要对应的集成包。例如安装 `langchain-anthropic`，在配置中填入自己可用的 Claude 型号和密钥后，可以这样创建客户端：

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model=config["model"],
    api_key=config["api_key"],
)
answer = model.invoke("你好")
print(answer.content)
```

Google 的集成类是 `ChatGoogleGenerativeAI`。如果使用本机 Ollama，可以安装 `langchain-ollama`，先下载要运行的模型，再使用下面的写法：

```python
from langchain_ollama import ChatOllama

model = ChatOllama(
    model=config["model"],
    base_url="http://localhost:11434",
)
answer = model.invoke("你好")
print(answer.content)
```

这些适配器都提供 `invoke()`，所以之后学习的消息和工具调用方式可以继续使用。本节任务先使用已经给出的 ChatOpenAI 连接代码，把发送问题和接收回答这一步练熟，其他适配器可以在自己的本地项目中按同样思路替换。
''', "编写一个能够接收用户问题并返回模型回答的函数。连接配置已经给出，请完成模型调用和返回值处理，让输入框中的不同问题都能交给模型回答。", '''
from langchain_openai import ChatOpenAI


def reply(config, question):
    model = ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    # 把 question 发给模型，再返回回答中的 content。
    raise NotImplementedError
''', "当你看到模型用自己的话回答问题，就说明已经完成第一次 API 调用了。回答内容可以与示例不同。", ["先调用 `model.invoke(question)`，得到的是消息对象。", "将消息保存到变量，再返回它的 `.content`。"], True)

lesson("stream_reply", "认识 Agent", "让回答逐段显示出来", '''
def stream_reply(model, question, on_text):
    pieces = []
    for chunk in model.stream(question):
        if chunk.content:
            on_text(chunk.content)
            pieces.append(chunk.content)
    return "".join(pieces)
''', '''
上一节的 `invoke()` 会等模型生成完整回答后才返回。流式调用 `stream()` 会不断返回小片段，我们可以收到一段就显示一段，这样回答区会随着模型生成内容逐渐更新。

```python
answer = model.invoke("介绍一下杭州。")
print(answer.content)

for chunk in model.stream("介绍一下杭州。"):
    print(chunk.content, end="", flush=True)
```

第一段代码在生成结束后显示完整回答，第二段会在生成过程中逐步显示内容。循环中的 `chunk` 保存刚收到的消息片段，`.content` 取出其中的文字，`end=""` 让相邻片段接在一起，`flush=True` 让终端及时显示。每个片段的长度由模型服务决定，可能只有几个字符，也可能包含较长的内容。

在网页里不能直接用终端的 `print` 更新回答区，所以任务给你一个 `on_text(text)` 函数。你每次调用它，网页就追加这段文字。与此同时，把收到的片段收集起来，最后用 `"".join(pieces)` 得到完整回答。

例如依次收到“杭州”“今天”“晴朗”，显示过程会逐步增长，函数最后返回“杭州今天晴朗”。这一节只处理文字，后面复现 Pi 时再学习如何合并工具调用的参数片段。
''', "补全 `stream_reply`，逐段调用 `on_text`，并返回所有文本拼接后的字符串。", '''
def stream_reply(model, question, on_text):
    pieces = []
    # 遍历 model.stream(question)，显示并保存每个文本片段。
    raise NotImplementedError
''', "看到回答逐段出现，结束后得到完整文本，就完成了流式输出。检查会核对拼接过程，不要求模型说出固定句子。", ["`model.stream(question)` 可以直接放在 `for` 循环里。", "每段文字先交给 `on_text`，再加入列表，循环结束后执行 `join`。"], True)

lesson("prompt_chain", "认识 Agent", "用提示模板组织问题", '''
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def make_chain(model):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "请用初学者能够理解的话解释概念。"),
        ("human", "请用一个生活中的例子解释：{topic}"),
    ])
    return prompt | model | StrOutputParser()
''', '''
提示模板可以保存重复使用的回答要求，例如解释概念时总要配上一个生活中的例子，调用时再填入本次需要解释的主题。这样更换问题时，已经写好的回答要求也会一起发送给模型。

`ChatPromptTemplate` 用来构建消息模板。`system` 写助手应当怎样回答，`human` 写这次用户的问题，`{topic}` 是等待填写的位置。

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "请用简单的话回答。"),
    ("human", "解释一下 {topic}，并给一个例子。"),
])

messages = prompt.invoke({"topic": "工具调用"})
answer = model.invoke(messages)
```

如果要重复做“填模板、调用模型、取出文字”这三步，可以用管道连接组件：

```python
chain = prompt | model | StrOutputParser()
text = chain.invoke({"topic": "工具调用"})
print(text)
```

这里的 `|` 把前一个组件的输出交给后一个组件，`StrOutputParser()` 把模型消息转成字符串。链的步骤由程序提前安排，而后面的 Agent 会根据模型提出的工具请求决定是否继续行动。
''', "完成 `make_chain(model)`，建立包含 `topic` 变量的提示模板，连接模型和字符串解析器，返回这条链。", '''
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def make_chain(model):
    # 创建模板，再返回 prompt | model | StrOutputParser()。
    raise NotImplementedError
''', "调用链时只填写一个 topic，就能收到围绕这个概念的解释。更换 topic 后，模型收到的问题也应随之变化。", ["模板中的变量写成 `{topic}`，调用时使用同名的字典键。", "将 `StrOutputParser()` 放在模型后面，它会从模型消息中取出文字，作为整条链的返回值。"], True, "工具调用")

lesson("weather_tool", "工具与 Agent", "编写实时天气查询工具", '''
import httpx
from langchain_core.tools import tool
from practice.weather_support import get_city_code, load_weather_config


@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气，city 为中文城市或区县名称。"""
    code = get_city_code(city)
    config = load_weather_config()
    response = httpx.get(
        config["url"],
        params={"areacode": code},
        headers={"X-APISpace-Token": config["api_key"]},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    realtime = data.get("result", {}).get("realtime", {})
    temperature = realtime.get("temp")
    weather = realtime.get("text")
    if temperature is None or not weather:
        raise ValueError("天气响应缺少温度或天气状况")
    return f"{city}：{weather}，{temperature}℃"
''', '''
天气接口接收城市编码，返回包含温度和天气状况的 JSON 数据。把查询过程封装成工具后，Agent 就能根据用户给出的城市获取实时天气，并将查询结果用于回答。

先在左侧文件栏打开 `.env`，填写自己的 `WEATHER_API_KEY`。它对应 APISpace 天气接口的访问凭证，与模型的 API Key 分开。`WEATHER_API_URL` 已经填入接口地址，单独运行本节不需要填写模型配置。接口的认证方式可以查阅 [APISpace 文档](https://www.apispace.com/eolink/api/456456/apiDocument)。

`practice/weather_support.py` 已提供两个辅助函数。`get_city_code(city)` 从同目录的 `weather_cities.csv` 查找城市编码，例如北京对应 101010100、杭州对应 101210101。找不到或名称重名时会抛出 ValueError，避免查询到另一个城市。`load_weather_config()` 从 `.env` 读取天气配置，返回包含 url 和 api_key 的字典。

```python
from practice.weather_support import get_city_code, load_weather_config

code = get_city_code("杭州")
print(code)  # 101210101
config = load_weather_config()
# config["url"] 是服务地址，config["api_key"] 只用于请求头。
```

服务返回的 JSON 中，`result.realtime.temp` 是温度，`result.realtime.text` 是天气状况。下面仅用一份响应示例观察字段读取，真正的函数需要从 HTTP 响应中取得这些数据。

```python
data = {"result": {"realtime": {"temp": 26.5, "text": "多云"}}}
realtime = data["result"]["realtime"]
print(realtime["temp"])  # 26.5
print(realtime["text"])  # 多云
```

`response.raise_for_status()` 会检查 HTTP 状态，认证失败或服务报错时抛出异常，`response.json()` 再把成功响应解析成 Python 字典。即使 HTTP 请求成功，也需要确认温度和天气字段存在，温度为 0 是有效值，不能用 `if not temperature` 判断缺失。

运行会发送真实天气请求，温度随时间改变。提交使用本地 HTTP 响应验证代码，会核对城市、请求头、超时和解析结果，也会模拟请求失败，不消耗天气接口额度。先把这个工具独立运行成功，下一节再让模型决定什么时候调用它。
''', "完成 get_weather，通过 HTTP 请求查询城市实时天气，读取温度和天气状况并返回文字。请求失败、响应缺少字段或城市无效时明确报错。", '''
import httpx
from langchain_core.tools import tool
from practice.weather_support import get_city_code, load_weather_config


@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气，city 为中文城市或区县名称。"""
    # 城市编码和配置读取已经提供，完成请求、状态检查与结果解析。
    raise NotImplementedError
''', "填写天气凭证后，运行可以显示接口当前返回的城市、天气和温度。提交通过后，还能确认代码正确处理了不同城市和失败响应。", ["先调用 get_city_code(city) 与 load_weather_config()，把编码放入 params，把凭证放入 X-APISpace-Token 请求头。", "调用 httpx.get 时指定 timeout=10，先 raise_for_status，再 json。", "从 result.realtime 读取 temp 与 text，使用 temperature is None 检查缺失，保留 0℃。"], True, "杭州")

lesson("weather_agent", "工具与 Agent", "搭建第一个 ReAct Agent", '''
from langchain.agents import create_agent
from practice.weather_tool import get_weather


def build_agent(model):
    return create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="天气问题请查询实时天气工具，依据工具结果回答，查询失败时明确说明。",
    )
''', '''
现在把前两部分接起来：模型负责理解问题，天气工具负责给出数据。`create_agent()` 会帮助我们完成“模型请求工具、程序执行工具、模型读取结果并回答”的循环。

```python
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="天气问题请查询工具。",
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "杭州的天气怎么样？"},
    ],
})
print(result["messages"][-1].content)
```

`model` 是已经创建的聊天模型，`tools` 是允许它使用的工具列表，`system_prompt` 提供回答要求。`invoke()` 传入用户消息，结果里的 `messages` 保存这次运行的消息，最后一条通常是最终回答。

这种根据观察结果继续选择行动的思路叫 **ReAct**。我们能够检查工具请求和工具结果，不需要要求模型暴露内部思考过程。模型也可以直接回答不需要工具的问题，因此一次 Agent 调用不一定会使用工具。

这里使用上一节完成的 `get_weather`，运行记录应当同时包含工具请求、查询得到的温度和模型根据温度生成的回答。检查会读取这些记录，确认数据确实经过了工具和模型。
''', "完成 `build_agent(model)`，把天气工具传给 `create_agent`，并提示模型在回答天气问题时查工具。", '''
from langchain.agents import create_agent
from practice.weather_tool import get_weather


def build_agent(model):
    # 用模型、工具列表和系统提示创建 Agent。
    raise NotImplementedError
''', "当你看到模型实际查询天气接口，并根据返回的天气与温度回答，就搭好了第一个能够使用实时数据的 Agent。", ["这里返回 Agent 对象即可，运行器会替你传入用户问题。", "`tools` 接收列表，列表里放工具对象 get_weather，不要先执行它。"], True, "请查询杭州现在的天气。")

lesson("structured", "工具与 Agent", "让回答变成可读取的数据", '''
from pydantic import BaseModel, Field


class TravelPlan(BaseModel):
    city: str = Field(description="目的地城市")
    days: int = Field(description="旅行天数")


def extract_plan(model, text):
    structured = model.with_structured_output(
        TravelPlan,
        method="function_calling",
    )
    return structured.invoke(text)
''', '''
如果用户说“我想去杭州玩三天”，后面的程序需要取出城市和天数。与其从一段自由回答里猜测，不如先告诉模型希望得到什么结构。

`BaseModel` 来自 Pydantic，用来描述并验证数据。`Field(description=...)` 的说明会帮助模型理解字段的含义。

```python
class TravelPlan(BaseModel):
    city: str = Field(description="目的地城市")
    days: int = Field(description="旅行天数")

planner = model.with_structured_output(
    TravelPlan,
    method="function_calling",
)
plan = planner.invoke("我想去杭州玩三天")
print(plan.city, plan.days)
```

`with_structured_output()` 创建一个带输出结构要求的调用对象，这里用 `function_calling` 通过模型的工具调用能力接收结构化数据。结果可以用 `.city` 和 `.days` 读取，不需要自己从回答中截取文字。它限制数据形状，但不能保证所有内容都正确，例如天数仍需要结合用户输入检查。

有些模型支持原生 JSON Schema，有些通过工具调用实现结构化输出，具体能力取决于模型适配器。本节先学习统一用法，检查使用固定输入验证字段能够被读取。
''', "完成 `extract_plan`，使用给定的 TravelPlan 描述结构，并返回模型得到的计划对象。", '''
from pydantic import BaseModel, Field


class TravelPlan(BaseModel):
    city: str = Field(description="目的地城市")
    days: int = Field(description="旅行天数")


def extract_plan(model, text):
    # 先设置结构，再传入 text。
    raise NotImplementedError
''', "能够分别读取 plan.city 和 plan.days，就说明回答已经成为后续程序可以使用的数据。", ["把 TravelPlan 这个类传给 `with_structured_output`。", "对返回的对象调用 `invoke(text)`，不需要自己拼 JSON。"], True, "我想去杭州玩三天。")

lesson("conversation", "工具与 Agent", "让对话记住上一轮", '''
from langchain_core.messages import HumanMessage


def chat(model, history, question):
    messages = [*history, HumanMessage(content=question)]
    answer = model.invoke(messages)
    return [*messages, answer]
''', '''
聊天界面看起来一直记得之前的话，其实通常是程序在下一次请求时重新发送了历史。单独创建一个聊天模型对象，并不会自动为所有调用保存对话。

```python
history = []
history = chat(model, history, "我叫小林。")
history = chat(model, history, "我刚才说自己叫什么？")
print(history[-1].content)
```

`chat()` 把前面创建消息和追加回答的步骤组合起来，接收旧历史和新问题后返回更新后的历史，调用方再保存这份返回值供下一轮使用。

这里的 `[*history, ...]` 会建立新列表，避免一个窗口的调用意外修改另一个地方持有的历史。你可以把它理解成“复制聊天记录，再补上这一轮”。后面会学习把这份记录放进检查点和会话文件。
''', "补全 chat，把旧历史、新问题和新回答按顺序放入新列表并返回。", '''
from langchain_core.messages import HumanMessage


def chat(model, history, question):
    # 建立新消息列表，调用模型，再追加回答。
    raise NotImplementedError
''', "第二轮模型能够依据上一轮的信息回答，同时原来的 history 列表没有被改动，就完成了最简单的短期记忆。", ["先在历史后追加 HumanMessage。", "模型返回后，把整条助手消息加入历史，不要只保存它的文字。"])

lesson("workflow", "用图控制流程", "用 LangGraph 连接两个步骤", '''
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    question: str
    answer: str


def build_workflow(model):
    def clean(state):
        return {"question": state["question"].strip()}

    def answer(state):
        message = model.invoke(state["question"])
        return {"answer": message.content}

    graph = StateGraph(State)
    graph.add_node("clean", clean)
    graph.add_node("answer", answer)
    graph.add_edge(START, "clean")
    graph.add_edge("clean", "answer")
    graph.add_edge("answer", END)
    return graph.compile()
''', '''
现在已经能直接调用模型。如果想先整理输入，再调用模型，就可以把两个步骤连接成一个工作流。LangGraph 用“节点”和“边”描述这个过程。

节点是处理某一步工作的函数，边连接前后步骤，状态 `State` 则保存这些步骤共同使用的数据。示例中的 TypedDict 描述了 question 和 answer 两个字段，运行时 state 是包含这些字段的字典，节点返回的字典会更新对应字段。

```python
graph = StateGraph(State)
graph.add_node("clean", clean)
graph.add_node("answer", answer)

graph.add_edge(START, "clean")
graph.add_edge("clean", "answer")
graph.add_edge("answer", END)

app = graph.compile()
result = app.invoke({"question": "  你好  "})
print(result["answer"])
```

`START` 和 `END` 标记开始与结束，`compile()` 把描述好的图变成可以运行的对象。这里的路线固定为整理输入后回答，下一节才加入条件分支。LangGraph 既能表达这种固定流程，也能表达 Agent 的工具循环。
''', "两个节点已经写好，请补上三条边，让流程按 clean、answer 的顺序执行并结束。", '''
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    question: str
    answer: str


def build_workflow(model):
    def clean(state):
        return {"question": state["question"].strip()}

    def answer(state):
        message = model.invoke(state["question"])
        return {"answer": message.content}

    graph = StateGraph(State)
    graph.add_node("clean", clean)
    graph.add_node("answer", answer)
    # 在这里连接 START、clean、answer 和 END。
    raise NotImplementedError
''', "输入两侧有空格时，模型收到整理后的问题，最后的状态里出现 answer，就说明两个节点成功连起来了。", ["`add_node` 注册节点，`add_edge` 才决定执行顺序。", "三条边分别是开始到 clean、clean 到 answer、answer 到结束。"])

lesson("routing", "用图控制流程", "给工作流增加一个分支", '''
def route(state):
    if state["need_tool"]:
        return "tools"
    return "answer"
''', '''
有些任务需要工具，有些可以直接回答。条件边会调用一个路由函数，根据当前状态选择下一个节点。

```python
def route(state):
    if state["need_tool"]:
        return "tools"
    return "answer"

graph.add_conditional_edges(
    "decide",
    route,
    {"tools": "tools", "answer": "answer"},
)
```

`route(state)` 返回的是路线名称，不需要在这里执行工具。`add_conditional_edges` 把路线名称与节点对应起来，图会调用选中的节点。

状态中的 `need_tool` 保存前一步作出的判断，路由函数根据这个布尔值选择工具节点或回答节点。接到模型以后，可以通过助手消息中 `tool_calls` 是否为空来得到这个判断，图的条件边会沿用同样的连接方式。
''', "完成 route。need_tool 为 True 时进入 tools，否则进入 answer。", '''
def route(state):
    # 根据 need_tool 返回下一步名称。
    raise NotImplementedError
''', "两种输入分别进入对应节点，而没有同时执行两条路线，就说明条件分支能够正常工作。", ["读取 `state[\"need_tool\"]`，它已经是布尔值。", "只返回字符串 tools 或 answer，不要调用同名函数。"])

lesson("checkpoint", "用图控制流程", "让图保存对话状态", '''
from langgraph.graph import StateGraph, MessagesState, START, END


def build_chat(model, saver):
    def answer(state):
        reply = model.invoke(state["messages"])
        return {"messages": [reply]}

    graph = StateGraph(MessagesState)
    graph.add_node("answer", answer)
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)
    return graph.compile(checkpointer=saver)
''', '''
上一轮的历史可以手动放在列表里，也可以交给图保存。LangGraph 的检查点会记录运行状态，`thread_id` 用来区分不同的对话。

```python
from langgraph.checkpoint.memory import InMemorySaver

app = build_chat(model, InMemorySaver())
config = {"configurable": {"thread_id": "chat-1"}}

app.invoke({"messages": [("user", "我叫小林")]}, config)
result = app.invoke(
    {"messages": [("user", "我叫什么？")]},
    config,
)
```

`MessagesState` 已经包含消息合并规则，因此节点只返回新增回答。相同线程继续之前的状态，不同线程相互独立。

`InMemorySaver` 适合练习，进程结束后数据会消失。需要重启后继续时，可以使用 `SqliteSaver` 把检查点写入数据库，Pi 的会话任务中会再实际使用磁盘存储。
''', "把传入的 saver 交给 compile，让图能够根据线程 ID 继续对话。", '''
from langgraph.graph import StateGraph, MessagesState, START, END


def build_chat(model, saver):
    def answer(state):
        reply = model.invoke(state["messages"])
        return {"messages": [reply]}

    graph = StateGraph(MessagesState)
    graph.add_node("answer", answer)
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)
    # 编译时接入 saver。
    raise NotImplementedError
''', "同一线程能接着聊，新线程没有混入旧消息，就说明对话状态保存正确。", ["检查点在编译图时配置。", "调用 `graph.compile(checkpointer=saver)`。"])

lesson("approval", "用图控制流程", "在执行前等一次确认", '''
from langgraph.types import interrupt


def approve(state):
    accepted = interrupt({"question": state["question"]})
    return {"approved": accepted is True}
''', '''
如果 Agent 准备修改文件，可以先展示操作内容，等待读者确认。LangGraph 的 `interrupt()` 会暂停执行，确认结果通过 `Command(resume=...)` 送回来。

```python
def approve(state):
    decision = interrupt({"question": "确认修改文件吗？"})
    return {"approved": decision is True}

# 使用同一个 config 恢复刚才暂停的图。
result = app.invoke(Command(resume=True), config)
```

`interrupt` 返回的 decision 来自恢复时传入的值。这个图需要检查点和线程 ID，才能知道恢复哪一次任务。恢复时暂停的节点会重新从开头执行，因此真正的写文件操作应放在确认之后。

例如恢复时传入 True，节点会返回 `{"approved": True}`，传入 False 时则返回 `{"approved": False}`。后面的文件修改节点可以读取这个字段，决定是否继续执行。
''', "实现 approve，展示 state.question 并等待确认。只有明确的 True 才把 approved 设成 True。", '''
from langgraph.types import interrupt


def approve(state):
    # 等待确认，再返回 approved 字段。
    raise NotImplementedError
''', "图先暂停，确认后返回 approved=True，取消后返回 False，就完成了最小的人工确认流程。", ["将需要展示的内容作为字典交给 interrupt。", "使用 `decision is True` 区分明确确认与其他输入。"])

lesson("rag", "检索与扩展", "先查资料，再让模型回答", '''
from langchain_core.messages import SystemMessage, HumanMessage


def ask_with_context(model, question, documents):
    context = "\\n".join(documents)
    messages = [
        SystemMessage(content="请只依据给定资料回答，资料不足时说明。"),
        HumanMessage(content=f"资料：\\n{context}\\n\\n问题：{question}"),
    ]
    return model.invoke(messages).content
''', '''
如果问题涉及项目自己的文档，模型未必知道答案。RAG 的做法是先从资料中找出相关片段，再把片段和问题一起交给模型。

```text
用户问题 → 检索相关资料 → 把资料加入提示 → 模型回答
```

例如资料写着“学习室周三晚上九点关闭”，我们把这句话交给模型，再问周三什么时候关门。模型不需要事先训练过这份文档，也能根据给定资料回答。

```python
documents = ["学习室周三晚上九点关闭。"]
answer = ask_with_context(
    model,
    "周三几点关门？",
    documents,
)
print(answer)
```

这一节先假设资料已经找好，重点学习怎样把资料放进消息。`documents` 是文本列表，`join` 将它们连成上下文，系统说明提醒模型在资料不足时直接说明。下一节再学习如何检索这些资料。
''', "完成 ask_with_context，把传入的资料与问题一起发送给模型，并返回回答文字。", '''
from langchain_core.messages import SystemMessage, HumanMessage


def ask_with_context(model, question, documents):
    # 组合资料与问题，再调用模型。
    raise NotImplementedError
''', "模型能根据给定资料说出周三晚上九点关门，就跑通了 RAG 中的“根据资料回答”这一步。", ["先用换行将 documents 拼成一段上下文。", "模型请求中应同时包含资料、问题和资料不足时的处理说明。"], True, "学习室周三几点关门？")

lesson("retriever", "检索与扩展", "用向量找到相关资料", '''
from langchain_core.vectorstores import InMemoryVectorStore


def build_retriever(embeddings, texts):
    store = InMemoryVectorStore.from_texts(
        texts,
        embedding=embeddings,
    )
    return store.as_retriever(search_kwargs={"k": 2})
''', '''
资料很多时，不能把全部内容都发给模型。向量模型会把文本转换成一组数字，相似内容的向量通常更接近，我们可以用这个关系找出相关片段。

聊天模型负责生成回答，向量模型负责把文字转成向量，它们承担不同的工作。下面的 embeddings 是已经创建的向量模型对象。

```python
store = InMemoryVectorStore.from_texts(
    ["学习室周三九点关闭", "食堂提供早餐", "学习室周末开放"],
    embedding=embeddings,
)

retriever = store.as_retriever(search_kwargs={"k": 2})
documents = retriever.invoke("学习室什么时候开放？")
print(documents[0].page_content)
```

`from_texts()` 为文本建立索引，`as_retriever()` 返回检索器，`k=2` 表示最多取两段资料。检索结果是 Document 对象，用 `.page_content` 读取正文，然后就能交给上一节的回答函数。

练习使用固定向量验证检索过程，不会调用付费向量服务。真实项目可以创建 `OpenAIEmbeddings(model=..., api_key=...)`，也可以选择本地向量模型。文档很长时还需要先切块，后面的 Pi 项目检索组件会提供分块实现。
''', "完成 build_retriever，为给定文本建立内存索引，并返回每次检索最多两段资料的检索器。", '''
from langchain_core.vectorstores import InMemoryVectorStore


def build_retriever(embeddings, texts):
    # 建立索引，再返回 k=2 的检索器。
    raise NotImplementedError
''', "查询学习室时，应当返回两段包含学习室信息的资料，后续的回答函数就可以使用这些内容解释开放时间。", ["把传入的 embeddings 交给 from_texts 的 embedding 参数。", "使用 `store.as_retriever(search_kwargs={\"k\": 2})`。"])

lesson("mcp_tools", "检索与扩展", "接入一个现成的 MCP 工具", '''
async def discover_tools(target, adapter_factory):
    async with adapter_factory(target) as adapter:
        return await adapter.list_tools()
''', '''
前面的天气工具由我们自己编写。如果其他程序已经提供了搜索或数据库工具，MCP 可以让 Agent 用统一方式发现和调用它们。

可以把 MCP 理解成工具服务之间的连接协议，LangChain 的 `MCPAdapter` 会把发现的工具转换成 LangChain 工具。

```python
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent

async def ask_service(model, target, question):
    async with MCPAdapter(target) as adapter:
        tools = await adapter.list_tools()
        agent = create_agent(model, tools=tools)
        return await agent.ainvoke({
            "messages": [("user", question)],
        })
```

`async with` 在进入时建立连接、离开时释放连接，`await` 等待工具发现完成。HTTP 地址适合远程服务，本地脚本可以用 Path 指定并通过 stdio 连接。MCP 只是提供工具，真正选择工具和处理结果的仍然是 Agent。

任务中的 adapter_factory 是用来创建适配器的函数。我们会传入一个本地替身，让你先学会连接的使用方式，不需要注册外部服务。
''', "完成 discover_tools，进入适配器的异步上下文，等待工具列表并返回，确保离开时正确关闭连接。", '''
async def discover_tools(target, adapter_factory):
    # 使用 async with 和 await 获取工具列表。
    raise NotImplementedError
''', "能够取得工具列表，而且成功和失败时都会离开连接上下文，就说明已经掌握了 MCP 接入的基本步骤。", ["先调用 adapter_factory(target) 创建适配器。", "在 async with 内执行 `await adapter.list_tools()`。"])

lesson("async_reply", "检索与扩展", "理解异步模型调用", '''
async def reply_async(model, question):
    answer = await model.ainvoke(question)
    return answer.content
''', '''
调用远程模型时，程序有一段时间在等待网络响应。异步写法允许它在等待期间处理其他任务，常见于网页服务。

```python
async def reply_async(model, question):
    answer = await model.ainvoke(question)
    return answer.content
```

`async def` 定义异步函数，`await` 等待结果。它不意味着模型本身生成得更快，也不意味着回答一定逐段返回。`ainvoke()` 是异步的完整回答，`astream()` 是异步的流式回答。

```python
async for chunk in model.astream("解释一下 Agent"):
    print(chunk.content, end="", flush=True)
```

普通 Python 脚本可以用 `asyncio.run(reply_async(...))` 开始执行，已经存在事件循环的环境通常直接使用 await。做到这里，你已经能够用基础组件搭建小型 Agent，接下来才开始拆解 Pi 的运行核心。
''', "完成 reply_async，等待 ainvoke 返回，再取出回答内容。", '''
async def reply_async(model, question):
    # 等待模型的完整回答。
    raise NotImplementedError
''', "调用并等待 reply_async 后，应当得到模型生成的文字，程序可以继续把这些文字显示到回答区。", ["异步模型接口叫 ainvoke。", "`answer = await model.ainvoke(question)`，然后返回 content。"])
