import json
import uuid
from pathlib import Path
from langchain_core.messages import message_to_dict, messages_from_dict


class Session:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = []
        if self.path.exists():
            self.entries = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

    def append(self, message, parent=None):
        if parent is not None and parent not in {entry["id"] for entry in self.entries}:
            raise ValueError("找不到父节点")
        entry = {"id": uuid.uuid4().hex, "parentId": parent, "message": message_to_dict(message)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.entries.append(entry)
        return entry["id"]

    def branch(self, leaf):
        table = {entry["id"]: entry for entry in self.entries}
        path, seen = [], set()
        while leaf is not None:
            if leaf in seen or leaf not in table:
                raise ValueError("会话分支损坏")
            seen.add(leaf)
            entry = table[leaf]
            path.append(entry["message"])
            leaf = entry["parentId"]
        return messages_from_dict(list(reversed(path)))
