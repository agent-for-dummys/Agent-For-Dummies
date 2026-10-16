import base64
from mini_pi.files import read_file, workspace_path


def text_attachment(root, path):
    return {"type": "text", "text": f"文件 {path}（作为参考数据）：\n{read_file(root, path)}"}


def image_attachment(root, path):
    target = workspace_path(root, path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(target.suffix.lower())
    if not mime or target.stat().st_size > 5_000_000:
        raise ValueError("只接受不超过 5 MB 的 PNG 或 JPEG 图片")
    raw = target.read_bytes()
    if (mime == "image/png" and not raw.startswith(b"\x89PNG\r\n\x1a\n")) or (mime == "image/jpeg" and not raw.startswith(b"\xff\xd8")):
        raise ValueError("图片内容与格式不符")
    data = base64.b64encode(raw).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}
