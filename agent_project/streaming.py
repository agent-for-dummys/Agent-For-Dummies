from langchain_core.messages import AIMessageChunk, message_chunk_to_message


def text_of(message):
    if isinstance(message.content, str):
        return message.content
    return "".join(block.get("text", "") for block in message.content
                   if isinstance(block, dict) and block.get("type") == "text")


def collect_stream(chunks, on_text=lambda text: None, cancelled=lambda: False):
    combined = None
    for chunk in chunks:
        if cancelled():
            raise InterruptedError("本轮运行已停止")
        text = text_of(chunk)
        if text:
            on_text(text)
        combined = chunk if combined is None else combined + chunk
    if combined is None:
        raise ValueError("模型没有返回任何流式片段")
    return message_chunk_to_message(combined)


async def collect_async(chunks, on_text=lambda text: None):
    combined = None
    async for chunk in chunks:
        text = text_of(chunk)
        if text:
            on_text(text)
        combined = chunk if combined is None else combined + chunk
    if combined is None:
        raise ValueError("模型没有返回任何流式片段")
    return message_chunk_to_message(combined)
