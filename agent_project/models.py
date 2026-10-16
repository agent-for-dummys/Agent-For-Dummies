"""A provider-independent model catalog; factories implement native adapters."""
class ModelRegistry:
    def __init__(self):
        self.providers = {}
        self.catalog = {}

    def register(self, provider, factory, models):
        if not provider or provider in self.providers:
            raise ValueError("厂商名称为空或已经注册")
        self.providers[provider] = factory
        for metadata in models:
            self.catalog[(provider, metadata["name"])] = dict(metadata)

    def create(self, provider, name, config, require_tools=True):
        metadata = self.catalog[(provider, name)]
        if require_tools and not metadata.get("tools", False):
            raise ValueError("这个模型不支持工具调用")
        return self.providers[provider]({**config, "model": name})

    def list_models(self):
        return [{"provider": provider, **metadata} for (provider, name), metadata in self.catalog.items()]
