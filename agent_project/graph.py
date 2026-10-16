from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
from mini_pi.context import window_context
from mini_pi.streaming import collect_stream
from mini_pi.tools import execute_calls
from mini_pi.limits import Budget


class State(TypedDict):
    messages: Annotated[list, add_messages]
    rounds: int
    tokens: int


def build_graph(model, tools, checkpointer, on_event=lambda event: None,
                before_tools=lambda state: None, cancelled=lambda: False,
                next_messages=lambda: [], max_rounds=8, context=None, max_tokens=20000):
    bound = model.bind_tools(tools)

    def model_node(state):
        if cancelled():
            raise InterruptedError("本轮运行已停止")
        budget = Budget(max_rounds, max_tokens)
        budget.calls = state.get("rounds", 0)
        budget.tokens = state.get("tokens", 0)
        budget.before_call()
        incoming = next_messages()
        history = state["messages"] + incoming
        request = context(history) if context else window_context(history)
        answer = collect_stream(bound.stream(request),
                                lambda text: on_event({"type": "text", "text": text}), cancelled)
        on_event({"type": "model_end", "usage": answer.usage_metadata or {}})
        budget.record(answer.usage_metadata or {})
        return {"messages": [*incoming, answer], "rounds": budget.calls, "tokens": budget.tokens}

    def tool_node(state):
        approved = before_tools(state)
        if approved is False:
            return {"messages": [ToolMessage(content="用户取消了修改，请停止修改并说明当前状态。", tool_call_id=call["id"], status="error") for call in state["messages"][-1].tool_calls]}
        if cancelled():
            raise InterruptedError("本轮运行已停止")
        return {"messages": execute_calls(state["messages"][-1], tools, on_event)}

    graph = StateGraph(State)
    graph.add_node("model", model_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", lambda state: "tools" if state["messages"][-1].tool_calls else END)
    graph.add_edge("tools", "model")
    return graph.compile(checkpointer=checkpointer)
