from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from mini_pi.files import read_file, write_file, edit_file
from mini_pi.limits import truncate_output
from mini_pi.diffs import preview_edit


def make_tools(root):
    @tool
    def read(path: str) -> str:
        """读取工作目录中的 UTF-8 文件，path 为相对路径。"""
        return read_file(root, path)

    @tool
    def write(path: str, content: str) -> str:
        """写入 UTF-8 文件，content 是文件的完整内容。"""
        return write_file(root, path, content)

    @tool
    def edit(path: str, old: str, new: str) -> dict:
        """把唯一匹配的 old 替换为 new，多个匹配时拒绝修改。"""
        preview = preview_edit(root, path, old, new)
        edit_file(root, path, old, new)
        return {"message": f"已修改 {path}", "diff": preview["patch"]}
    return [read, write, edit]


def execute_calls(message, tools, on_event=lambda event: None):
    registry = {item.name: item for item in tools}
    results = []
    for call in message.tool_calls:
        on_event({"type": "tool_start", "name": call["name"], "id": call["id"]})
        try:
            value = registry[call["name"]].invoke(call["args"])
            result = ToolMessage(content=truncate_output(str(value)), tool_call_id=call["id"])
        except Exception as error:
            result = ToolMessage(content=f"{type(error).__name__}: {error}",
                                 tool_call_id=call["id"], status="error")
        results.append(result)
        on_event({"type": "tool_end", "name": call["name"], "id": call["id"], "status": result.status})
    return results
