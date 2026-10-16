"""Offline model used only for smoke tests and the explicit demo mode."""
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage


class DemoModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        if isinstance(messages[-1], ToolMessage):
            return AIMessage(content="已读取文件：\n" + messages[-1].content)
        return AIMessage(content="", tool_calls=[{"name": "read", "args": {"path": "hello.py"}, "id": "demo-read", "type": "tool_call"}])

    def stream(self, messages):
        answer = self.invoke(messages)
        if answer.tool_calls:
            yield AIMessageChunk(content="", tool_calls=answer.tool_calls)
        else:
            for text in [answer.content[:6], answer.content[6:]]:
                yield AIMessageChunk(content=text)
