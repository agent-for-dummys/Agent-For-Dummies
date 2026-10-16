from langchain_core.messages import SystemMessage, HumanMessage


def make_messages(question, history=(), system="你是帮助用户理解和修改代码的助手。"):
    if not question.strip():
        raise ValueError("问题不能为空")
    return [SystemMessage(content=system), *history, HumanMessage(content=question)]


def ask(model, question, history=()):
    return model.invoke(make_messages(question, history))
