"""Native local command extension. The web runner uses its bounded adapter."""
import subprocess
import sys
from langchain_core.tools import tool
from mini_pi.files import workspace_path


def run_python(root, path, timeout=5):
    target = workspace_path(root, path)
    if target.suffix != ".py":
        raise ValueError("这里只运行 Python 文件")
    completed = subprocess.run([sys.executable, "-I", str(target)], cwd=root,
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=timeout, shell=False)
    return {"returncode": completed.returncode, "stdout": completed.stdout[-10000:], "stderr": completed.stderr[-10000:]}


def command_tool(root):
    @tool
    def run(path: str) -> dict:
        """运行工作目录中的 Python 文件，返回退出码、标准输出和错误输出。"""
        return run_python(root, path)
    return run
