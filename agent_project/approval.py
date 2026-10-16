from langgraph.types import interrupt, Command


def confirm_tools(state):
    changes = [call for call in state["messages"][-1].tool_calls if call["name"] in {"write", "edit", "run"}]
    if changes:
        decision = interrupt({"type": "approval", "calls": changes})
        if decision is not True:
            return False
    return True


def resume_graph(graph, thread_id, approved):
    return graph.invoke(Command(resume=approved), {"configurable": {"thread_id": thread_id}})
