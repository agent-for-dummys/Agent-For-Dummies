"""Provider configuration for the Python mini-pi reconstruction."""
from pathlib import Path
from dotenv import dotenv_values
from langchain_openai import ChatOpenAI


def load_config(path=".env"):
    values = dict(dotenv_values(Path(path), interpolate=False))
    provider = (values.get("MODEL_PROVIDER") or "openai").lower()
    prefix = {"openai": "OPENAI", "zhipu": "ZHIPUAI"}.get(provider, provider.upper())
    key = values.get("MODEL_API_KEY") or values.get(f"{prefix}_API_KEY") or ""
    model = values.get("MODEL_NAME") or values.get(f"{prefix}_MODEL") or ""
    if not key or not model:
        raise ValueError("请在 .env 中填写 MODEL_API_KEY 和 MODEL_NAME")
    base = values.get("MODEL_BASE_URL") or values.get(f"{prefix}_BASE_URL") or {
        "openai": "https://api.openai.com/v1", "zhipu": "https://open.bigmodel.cn/api/paas/v4/"
    }.get(provider, "")
    if not base:
        raise ValueError("自定义厂商需要填写 MODEL_BASE_URL")
    return {"provider": provider, "api_key": key, "model": model, "base_url": base}


def create_model(config):
    # Only standard Chat Completions fields are shared across these providers.
    return ChatOpenAI(
        model=config["model"], api_key=config["api_key"],
        base_url=config["base_url"], timeout=30, max_retries=2,
        use_responses_api=False, stream_usage=False,
    )
