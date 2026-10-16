import json
import time
from pathlib import Path


def redact(value):
    if isinstance(value, dict):
        return {key: "[redacted]" if any(word in key.lower() for word in ("key", "secret", "authorization")) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class Trace:
    def __init__(self, path):
        self.path = Path(path)
        self.tokens = 0
        self.events = []

    def record(self, event):
        value = redact({"time": time.time(), **event})
        self.tokens += event.get("usage", {}).get("total_tokens", 0)
        self.events.append(value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")
