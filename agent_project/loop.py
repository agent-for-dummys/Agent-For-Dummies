from mini_pi.tools import execute_calls


def agent_loop(model, tools, messages, max_rounds=8):
    history = list(messages)
    bound = model.bind_tools(tools)
    for _ in range(max_rounds):
        answer = bound.invoke(history)
        history.append(answer)
        if not answer.tool_calls:
            return history
        history.extend(execute_calls(answer, tools))
    raise RuntimeError("达到最大模型调用轮数")
