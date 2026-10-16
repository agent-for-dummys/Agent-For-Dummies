from pathlib import Path
from mini_pi.files import read_file, workspace_path


def project_instructions(root, relative="."):
    root = Path(root).resolve()
    target = workspace_path(root, relative)
    if target.is_file():
        target = target.parent
    directories = [root]
    if target != root:
        directories += list(reversed([target, *[p for p in target.parents if p != root and p.is_relative_to(root)]]))
    sections = []
    for directory in directories:
        file = directory / "AGENTS.md"
        if file.exists():
            path = file.relative_to(root).as_posix()
            sections.append(f"项目说明 {path}：\n{read_file(root, path)}")
    return "\n\n".join(sections)
