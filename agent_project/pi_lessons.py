"""Apply the beginner concepts to small, explicit Pi reconstruction tasks."""
PI_LESSONS = [
    dict(id="pi_model", group="拆解 Pi 的运行循环", title="为 Pi 接上模型接口",
         target="config", focus="create_model", live=False,
         lesson="""
前面的小任务已经用过 `ChatOpenAI`，现在把创建模型的代码放进项目自己的 `config.py`，让终端入口、Agent 循环和其他组件都通过同一个入口取得模型。

Pi 的模型层负责处理不同服务的差异。我们的 `load_config()` 已经提供好，它读取 `.env` 并返回包含 `model`、`api_key` 和 `base_url` 的字典。把这个字典传给 `create_model(config)` 后，应当得到一个能够调用 `invoke()`、`stream()` 和 `bind_tools()` 的聊天模型对象，供后面的循环和工具组件使用。

```python
config = load_config(".env")
model = create_model(config)
answer = model.invoke("你好")
print(answer.content)
```

基础用法与第一节相同，这次增加 `timeout=30` 和 `max_retries=2`：前者限制一次请求等待的时间，后者允许连接暂时失败时重试。兼容 Chat Completions 的服务使用相同适配器，原生协议不同的服务可以在项目的模型目录中注册自己的创建函数。

示例中的 `use_responses_api=False` 固定使用 Chat Completions，`stream_usage=False` 避免向未支持该扩展的兼容服务请求流式用量。这两个选项用于当前兼容接口，使用其他厂商的原生适配器时，需要根据该适配器支持的参数进行配置。
""", task="完成 create_model，把配置字段交给模型类，并保留示例中的超时与兼容选项。", success="其他文件通过 create_model 取得聊天模型后，可以继续使用 invoke、stream 和 bind_tools，连接配置也能够在这个入口集中调整。",
         hints=["返回模型对象，不要在创建函数中发送问题。", "每个构造参数单独写一行，可以更清楚地核对配置字段。"]),
    dict(id="pi_files", group="拆解 Pi 的运行循环", title="让 Pi 精确修改一个文件",
         target="files", focus="edit_file", live=False,
         lesson="""
编程 Agent 需要先读文件，再定位修改位置。Pi 的文件工具也围绕读取、写入和编辑展开，我们先完成其中最容易观察的一项：替换一个明确的文本片段。

项目中的 `read_file(root, path)` 返回工作目录里的文本，`write_file(root, path, content)` 写入完整文本，路径检查已经提供。`edit_file(root, path, old, new)` 会组合这些已有操作，根据 old 定位文本，再把对应位置改成 new。

```python
# hello.py 原来包含：print("Hello")
edit_file(
    root,
    "hello.py",
    old="Hello",
    new="你好",
)
# 修改后应包含：print("你好")
```

当 `old` 出现多次时，模型可能没有给足定位信息，因此不要随意选择第一处。要求它恰好出现一次，才能把修改准确落到指定位置。没有匹配或目标为空时也应该停止修改。

之后的工具组件会调用这个文件层，差异预览和撤销的辅助实现也放在项目中，可以在学会基本编辑之后继续阅读。
""", task="读取文件，检查 old 恰好出现一次，再替换为 new 并写回。拒绝修改时保持原文件不变。", success="唯一匹配时文件正确改变，重复匹配时原文件保持不变，就完成了一个可供 Agent 使用的编辑动作。",
         hints=["先读出文本，用 content.count(old) 检查匹配次数。", "old 为空或匹配次数不等于一时抛出 ValueError，检查通过后再写入。"]),
    dict(id="pi_tools", group="拆解 Pi 的运行循环", title="把模型的工具请求执行起来",
         target="tools", focus="execute_calls", live=False,
         lesson="""
天气 Agent 中的 `create_agent` 已经替我们处理过工具调用，现在把这一部分拆开。模型会返回希望调用的工具名称和参数，程序收到这些请求后，再查找并执行对应的 Python 函数。

```python
call = {
    "name": "read",
    "args": {"path": "hello.py"},
    "id": "call-1",
}
tool = registry[call["name"]]
value = tool.invoke(call["args"])
```

`registry` 是名称到工具对象的字典。执行以后，要把结果装进 `ToolMessage`，并保留原来的调用 ID：

```python
result = ToolMessage(
    content=str(value),
    tool_call_id=call["id"],
)
```

`execute_calls(message, tools, on_event)` 接收助手消息、工具列表和事件回调，返回对应的工具消息列表。一次助手消息可能请求多个工具，因此需要逐个处理。工具失败时也应返回带有原调用 ID 的错误消息，让模型知道哪次操作没有完成，并据此调整下一步。

文件中已经提供 `make_tools()`，它把上一节的文件操作包装成 LangChain 工具。分发函数通过这些工具对象执行请求，再把结果交回模型。
""", task="执行 message.tool_calls 中的全部请求，保留顺序与 ID，并产生工具开始和结束事件。", success="模型发来的每个调用都得到对应 ToolMessage，即使工具失败也能知道是哪一次调用失败了。",
         hints=["先用工具的 name 建立字典，再遍历 message.tool_calls。", "异常时使用 status='error' 的 ToolMessage，tool_call_id 仍使用原请求 ID。"]),
    dict(id="pi_loop", group="拆解 Pi 的运行循环", title="亲手写出 Pi 的 Agent 循环",
         target="loop", focus="agent_loop", live=False,
         lesson="""
现在我们已经有模型接口和工具执行函数，可以自己实现之前由 `create_agent` 提供的循环。这个过程是 Pi 运行核心的重要部分。

```text
调用模型 → 保存助手消息
              ↓ 有工具请求
           执行工具 → 保存工具结果 → 再调用模型
              ↓ 没有工具请求
           返回完整对话
```

`agent_loop(model, tools, messages, max_rounds)` 返回本轮完成后的消息历史。先复制传入的消息，再通过 `bind_tools(tools)` 告诉模型有哪些工具。每轮都先加入助手消息，随后才加入工具结果。

例如用户要求解释 `hello.py`，第一轮模型请求读取，第二轮模型看到文件正文后组织解释。只有没有工具调用时才结束，否则工具结果还需要送回模型。

`max_rounds` 限制模型调用次数，避免一直请求工具而停不下来。这里按顺序执行工具，后续再考虑并发或更复杂的调度。
""", task="连接模型与 execute_calls，直到没有工具调用时返回历史，并在达到轮数上限时停止。", success="轨迹中出现“模型请求读取 → 工具返回文件 → 模型解释文件”，就说明你已经写出了真正的工具循环。",
         hints=["不要执行工具后直接返回，模型还需要阅读工具结果。", "每轮都把助手消息与对应 ToolMessage 加入历史，再进入下一次循环。"]),
    dict(id="pi_context", group="让 Pi 持续工作", title="给长对话保留合适的上下文",
         target="context", focus="window_context", live=False,
         lesson="""
对话越来越长时，不能一直把全部消息发送给模型。Pi 会压缩上下文，我们先实现容易理解的窗口策略，再观察摘要策略的差别。

`window_context(messages, keep_turns)` 保留系统说明与最近几轮完整对话。这里的“一轮”从用户消息开始，包括这轮产生的助手消息和工具结果。不能把工具请求留下却删掉对应结果。

```python
# 原来有五轮完整对话。
recent = window_context(messages, keep_turns=2)
# recent 包含系统说明和最近两轮。
```

`split_turns()` 已经把消息分组，返回系统消息列表和轮次列表。你的任务是选出需要保留的轮次，再展平成消息列表。

同一文件还提供 `summary_context()`：让模型概括旧轮次，再保留近期完整消息。窗口策略简单、无需额外调用，摘要策略能保留更多早期信息，但摘要可能遗漏细节，因此完整会话仍应保存在磁盘上。
""", task="完成 window_context，保留系统消息与最近 keep_turns 轮，不修改原始历史。", success="缩短后的请求没有打断工具配对，最近的问题也没有丢失，就说明窗口上下文处理正确。",
         hints=["先调用 split_turns，系统消息与对话轮次需要分开处理。", "选择 turns[-keep_turns:]，再把这些轮次里的消息按原顺序展开。"]),
    dict(id="pi_session", group="让 Pi 持续工作", title="从会话记录恢复一条分支",
         target="sessions", focus="Session.branch", live=False,
         lesson="""
Pi 不只保存一条聊天列表，它还允许从过去某个位置继续尝试另一种做法。每条会话记录有自己的 ID 和父节点 ID，因此可以组成一棵树。

```text
问题 a
 ├─ 回答 b
 └─ 新尝试 c
```

`Session.append(message, parent)` 已经提供，会把消息追加到 JSONL 文件并返回新 ID。`branch(leaf)` 的任务是从末尾节点向上找到父节点，恢复从根到末尾的消息列表。

```python
session = Session("session.jsonl")
a = session.append(HumanMessage(content="解释代码"))
b = session.append(AIMessage(content="第一种解释"), a)
c = session.append(AIMessage(content="另一种解释"), a)

history = session.branch(c)
```

这时 history 的路径是 `[a, c]`，调用 `branch(b)` 则可以取得另一条路径 `[a, b]`。磁盘上的其他分支不会被删除，用户可以再回到它们。消息保存和恢复使用 LangChain 的转换函数，以保留角色与工具调用信息。
""", task="完成 Session.branch，沿 parentId 追溯，检查不存在的节点和循环引用，再按正向顺序恢复消息。", success="重开会话文件后，选择不同末尾 ID 能恢复不同路径，就实现了 Pi 式会话分支的基础。",
         hints=["先把 entries 转成 id 到记录的字典，查找父节点会更直接。", "追溯得到的是倒序，恢复消息前要反转，并用 seen 检查是否重复遇到同一个节点。"]),
    dict(id="pi_graph", group="让 Pi 持续工作", title="把工具循环接到 LangGraph",
         target="graph", focus="edges", live=False,
         lesson="""
手写循环已经能够工作，现在把它放进 LangGraph，接上之前学过的检查点与人工确认。文件中已经提供模型节点和工具节点，接下来通过边描述它们的执行顺序，并根据模型返回的工具请求选择下一步。

模型节点返回新的助手消息，工具节点返回对应工具结果。条件边检查最新助手消息是否有 `tool_calls`，有就进入工具节点，没有就结束。

```python
graph.add_edge(START, "model")
graph.add_conditional_edges(
    "model",
    lambda state: (
        "tools"
        if state["messages"][-1].tool_calls
        else END
    ),
)
graph.add_edge("tools", "model")
```

与基础工作流相比，这次多了一条回到模型的边，因此能够执行多轮行动。编译时传入 checkpointer，暂停或续聊才能找到原来的状态。

模型节点内部使用前面介绍的窗口上下文、流式聚合和预算检查，工具节点使用你完成的工具分发函数。它们现在开始在同一个项目里配合工作。
""", task="补全 build_graph 最后的连接部分，使模型能进入工具、工具能回到模型，并接入检查点。", success="图能够完成读取和回答，换线程时保持独立，重新使用同一检查点时能继续，就完成了项目编排。",
         hints=["START 指向 model，tools 需要回到 model。", "编译时使用 graph.compile(checkpointer=checkpointer)，不要建立新的无关 saver。"]),
    dict(id="pi_skills", group="扩展与组装", title="让 Pi 按需读取技能说明",
         target="skills", focus="skill_tool", live=False,
         lesson="""
有些能力不需要写进核心循环，例如代码审查的步骤可以保存在技能文件里。Pi 会先告诉模型有哪些技能，再在需要时加载具体说明。

`discover_skills(root)` 已经提供技能目录，包含名称、描述和文件路径。`skill_tool(root)` 要返回一个 LangChain 工具，让模型用名称取得技能全文。

```python
loader = skill_tool("workspace/skills")
instructions = loader.invoke({"name": "review"})
print(instructions)
```

这里又用到了你在天气任务中学过的 `@tool`，只是工具返回的内容变成了操作说明。技能加载后，Agent 仍然通过现有文件工具执行具体动作，技能文件本身不会自动变成 Python 程序。

同一项目还提供提示模板与事件钩子，MCP 工具可以通过 extra_tools 接入。这些扩展通过现有工具入口向循环提供能力，加载技能说明和执行文件操作能够继续使用相同的消息与工具结果格式。
""", task="返回一个名为 load_skill 的工具，按目录中的名称读取对应技能全文。", success="初始提示中包含技能描述，模型选定技能后再调用加载工具取得完整步骤，这样每次请求只携带当前需要的内容。",
         hints=["先调用 discover_skills(root) 保存目录。", "在内部定义带 @tool 的 load_skill(name)，返回目录中对应路径的文本。"]),
    dict(id="pi_events", group="扩展与组装", title="把运行事件交给界面", target="events", focus="EventDecoder.feed", live=False,
         lesson="""
终端和网页都需要显示模型文字、工具开始与工具完成。Pi 提供事件接口，我们用一行一个 JSON 的方式表示这些变化。

```text
{"type": "text", "text": "正在读取"}
{"type": "tool_end", "name": "read"}
```

网络收到的片段不一定刚好是一行，可能只有半行，也可能一次包含多行。`EventDecoder.feed(text)` 需要把片段加入缓存，遇到完整换行后才解析 JSON，返回这次已经收齐的事件列表。

```python
decoder = EventDecoder()
decoder.feed('{"type": "te')
events = decoder.feed('xt", "text": "你好"}\\n')
```

第一次调用时，缓存里还没有完整的一行，因此返回空列表，第二次补齐内容和换行后，才能解析出完整事件。编码函数和连接结束检查已经提供，feed 负责在两次调用之间保存尚未收齐的内容。
""", task="完成 feed，处理半行、多行和空行，保留尚未完成的尾部。", success="相同事件无论被拆成几次传输，最终都能按顺序恢复，界面就不会因网络片段边界而丢字或报错。",
         hints=["先把本次 text 追加到 self.pending。", "只要缓存中还有换行，就取出一行解析，剩下的内容继续留在缓存里。"]),
    dict(id="pi_limits", group="扩展与组装", title="让 Agent 知道什么时候停止", target="limits", focus="Budget.before_call", live=False,
         lesson="""
如果模型一直请求工具，Agent 就可能一直运行。Pi 式运行环境需要有停止条件，我们先用调用次数和累计 token 数控制每轮任务。

`Budget(max_calls, max_tokens)` 保存上限，`record(usage)` 已经提供，会根据模型返回的使用量累计 token。你的任务是在下一次调用开始前检查预算。

```python
budget = Budget(max_calls=3, max_tokens=5000)
budget.before_call()
answer = model.invoke(messages)
budget.record(answer.usage_metadata or {})
```

`before_call()` 应在达到任一上限时抛出异常，没有达到时才增加调用次数。请求失败也消耗过一次尝试，所以次数不能只在成功后增加。

文件里还提供工具输出裁剪与粗略 token 估计，模型节点已经接好了这个预算组件。这里限制的是运行过程，真实费用还取决于模型服务的计费规则。
""", task="实现 before_call，在请求前检查两种上限，并正确累计本次尝试。", success="允许的次数用完后，下一次请求被阻止，正常的小任务仍能完成，就给循环加上了明确的边界。",
         hints=["达到上限也应该停止，比较时使用 >=。", "两个条件都检查完以后，再增加 self.calls。"]),
    dict(id="pi_evaluate", group="扩展与组装", title="检查 Agent 是否真的完成任务", target="evaluation", focus="evaluate_run", live=False,
         lesson="""
不同模型可能用不同的话描述同一个结果，所以判断编程任务不能只比较一句回答。更可靠的方法是检查它做了什么，以及文件最后变成了什么样。

`evaluate_run(events, required_tools, expected_files, actual_files)` 接收运行事件、必须完成的工具和两份文件内容，返回各项检查与整体结果。

```python
report = evaluate_run(
    events,
    required_tools=["read", "edit"],
    expected_files={"hello.py": expected_code},
    actual_files={"hello.py": actual_code},
)
print(report["passed"])
```

只有成功的 `tool_end` 才表示工具完成，`tool_start` 只是开始执行。最终文件也要符合目标，不能因为 Agent 说“修改好了”就当作完成。

""", task="分别检查成功工具与文件结果，并返回包含 passed、tools_ok、files_ok 和 model_calls 的报告。", success="正确修改能够通过，工具失败或文件没有改变时无法通过，就具备了验证整个 Agent 的基础。",
         hints=["先筛选 type 为 tool_end 且 status 为 success 的事件。", "整体通过需要工具检查与文件检查同时成立。"]),
]
