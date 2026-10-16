import json


def encode_event(event):
    if not isinstance(event.get("type"), str):
        raise ValueError("事件需要字符串 type")
    return json.dumps(event, ensure_ascii=False) + "\n"


class EventDecoder:
    def __init__(self):
        self.pending = ""

    def feed(self, text):
        self.pending += text
        result = []
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    raise ValueError("事件格式不正确")
                result.append(event)
        return result

    def finish(self):
        if self.pending.strip():
            raise ValueError("最后一条事件不完整")
