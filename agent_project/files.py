from pathlib import Path


def workspace_path(root, path):
    root = Path(root).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or ".env" in target.parts:
        raise ValueError("文件必须位于工作目录中，而且不能读取 .env")
    return target


def read_file(root, path):
    target = workspace_path(root, path)
    if target.stat().st_size > 100_000:
        raise ValueError("文件超过 100 KB，请先缩小读取范围")
    return target.read_text(encoding="utf-8")


def write_file(root, path, content):
    target = workspace_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入 {path}"


def edit_file(root, path, old, new):
    content = read_file(root, path)
    if not old or content.count(old) != 1:
        raise ValueError("old 必须在文件中恰好出现一次")
    return write_file(root, path, content.replace(old, new, 1))
