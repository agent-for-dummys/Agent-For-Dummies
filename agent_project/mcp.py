async def load_mcp_tools(target, adapter_factory=None):
    if adapter_factory is None:
        from langchain.mcp import MCPAdapter
        adapter_factory = MCPAdapter
    async with adapter_factory(target) as adapter:
        return await adapter.list_tools()
