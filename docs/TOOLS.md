# JARVIS Tool Development Guide

## Built-in Tools

| Tool | Class | Purpose |
|------|-------|---------|
| `browser` | `BrowserTool` | Browser automation |
| `file_manager` | `FileManagerTool` | File I/O |
| `web_search` | `WebSearchTool` | DuckDuckGo search |
| `document_processor` | `DocumentProcessorTool` | Read documents |
| `system_monitor` | `SystemMonitorTool` | OS metrics |

## Creating a Custom Tool

1. Subclass `ToolBase` in `jarvis/core/tools/`
2. Implement `execute(**kwargs)` and `schema` property
3. Register via `PluginLoader.register(MyTool())`

```python
from jarvis.core.tools.tool_base import ToolBase

class MyTool(ToolBase):
    def __init__(self):
        super().__init__(name="my_tool", description="Does something useful")

    @property
    def schema(self):
        return {
            "name": "my_tool",
            "parameters": {"query": {"type": "string"}},
            "required": ["query"],
        }

    async def execute(self, **kwargs):
        query = kwargs.get("query", "")
        # do work
        return self._success({"result": f"Processed: {query}"})
```

## Plugin Loading

Place your tool file in the `plugins/` directory.
Set `auto_load: true` in `config/tools.yaml` or call:

```python
loader = PluginLoader()
loader.load_from_directory(Path("plugins/"))
```
