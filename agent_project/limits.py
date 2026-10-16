from mini_pi.streaming import text_of


class Budget:
    def __init__(self, max_calls=20, max_tokens=20000):
        self.max_calls = max_calls
        self.max_tokens = max_tokens
        self.calls = 0
        self.tokens = 0

    def before_call(self):
        if self.calls >= self.max_calls or self.tokens >= self.max_tokens:
            raise RuntimeError("运行预算已用完")
        self.calls += 1

    def record(self, usage):
        self.tokens += max(0, usage.get("total_tokens", 0))


def truncate_output(text, limit=10000):
    if limit < 0:
        raise ValueError("limit 不能为负数")
    return text if len(text) <= limit else text[:limit] + "\n[输出已截断，请缩小读取范围]"


def estimate_tokens(messages):
    # A rough local estimate; actual usage comes from the model response.
    text = "".join(text_of(message) for message in messages)
    return sum(1 if ord(char) > 127 else .25 for char in text).__ceil__()
