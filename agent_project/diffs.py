import difflib
import hashlib
from mini_pi.files import read_file, write_file


def preview_edit(root, path, old, new):
    before = read_file(root, path)
    if not old or before.count(old) != 1:
        raise ValueError("编辑目标必须唯一")
    after = before.replace(old, new, 1)
    patch = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                       fromfile=path, tofile=path))
    return {"path": path, "before": before, "after": after, "digest": hashlib.sha256(before.encode()).hexdigest(), "patch": patch}


def apply_preview(root, preview):
    current = read_file(root, preview["path"])
    if hashlib.sha256(current.encode()).hexdigest() != preview["digest"]:
        raise ValueError("文件在预览后发生了变化，请重新生成修改")
    return write_file(root, preview["path"], preview["after"])


def undo_preview(root, preview):
    if read_file(root, preview["path"]) != preview["after"]:
        raise ValueError("文件有新的修改，不能直接撤销")
    return write_file(root, preview["path"], preview["before"])
