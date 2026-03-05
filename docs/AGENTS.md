# JARVIS Agent System

## Overview

JARVIS uses a hierarchical multi-agent architecture where specialised agents handle
different aspects of a user request.

## Agent Hierarchy

```
CommanderAgent (coordinator)
├── PlannerAgent         → breaks goals into steps
├── ReasoningAgent       → chain-of-thought logic
├── ResearchAgent        → information synthesis
├── CodingAgent          → code generation
├── DataProcessingAgent  → data analysis
├── ContentGenerationAgent → creative content
├── BrowserToolAgent     → browser automation
├── FileToolAgent        → file system
└── SearchToolAgent      → web search
```

## Message Bus

Agents communicate via the `MessageBus` pub/sub system:

```python
bus = MessageBus()
bus.subscribe(MessageType.EVENT, my_handler)
await bus.publish(Message(MessageType.COMMAND, "agent_name", {"key": "value"}))
```

**Message Types:** `COMMAND`, `QUERY`, `RESPONSE`, `EVENT`

## Adding a New Agent

1. Create a file in `jarvis/core/agents/`
2. Subclass `AgentBase`
3. Implement the `run(task)` async method
4. Register in the agent config (`config/agents.yaml`)

```python
from jarvis.core.agents.agent_base import AgentBase

class MyAgent(AgentBase):
    async def run(self, task):
        # do work
        return self._success({"result": "done"})
```
