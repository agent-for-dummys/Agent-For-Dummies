from collections import deque
from threading import Event, Lock
from langchain_core.messages import HumanMessage


class Control:
    def __init__(self):
        self.stop = Event()
        self.lock = Lock()
        self.steering = deque()
        self.followups = deque()

    def enqueue(self, text, kind="steer"):
        if kind not in {"steer", "followup"} or not text.strip():
            raise ValueError("消息类型或内容不正确")
        with self.lock:
            (self.steering if kind == "steer" else self.followups).append(text)

    def take(self, kind="steer"):
        with self.lock:
            target = self.steering if kind == "steer" else self.followups
            messages = [HumanMessage(content=text) for text in target]
            target.clear()
        return messages

    def cancel(self):
        self.stop.set()
