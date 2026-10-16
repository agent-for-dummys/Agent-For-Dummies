from pathlib import Path
from langchain_core.tools import tool


def discover_skills(root):
    result = {}
    for path in sorted(Path(root).glob("*/SKILL.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        description = next((line for line in lines if line.strip() and not line.startswith("#")), "")
        result[path.parent.name] = {"description": description, "path": path}
    return result


def skill_tool(root):
    catalog = discover_skills(root)
    @tool
    def load_skill(name: str) -> str:
        """按名称加载技能完整说明，name 必须来自技能目录。"""
        return catalog[name]["path"].read_text(encoding="utf-8")
    return load_skill


def expand_prompt(template, variables):
    return template.format_map(variables)


class Hooks:
    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, event):
        for handler in self.handlers.get(event["type"], []):
            handler(dict(event))
