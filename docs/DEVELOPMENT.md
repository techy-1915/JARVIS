# JARVIS Development Guide

## Project Structure

```
jarvis/
├── core/
│   ├── brain/       ← AI model integration
│   ├── agents/      ← Multi-agent system
│   ├── memory/      ← Memory layers
│   ├── tools/       ← Tool plugins
│   ├── security/    ← Security modules
│   ├── execution/   ← Action execution
│   ├── perception/  ← Input processing
│   └── output/      ← Response generation
├── api/             ← FastAPI server
│   └── routes/
├── interface/       ← Web dashboard
├── mobile_app/      ← Mobile specs
├── config/          ← Configuration
├── tests/           ← Test suite
├── docs/            ← This documentation
└── logs/            ← Runtime logs
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Code Style

- Python 3.10+ type hints throughout
- Docstrings on all public classes and functions (Google style)
- `async/await` for all I/O operations
- Use `logging` (never `print`) for diagnostics
- Each module should be independently importable

## Adding a New Module

1. Create the module file in the appropriate `core/` subdirectory
2. Add it to the package `__init__.py` if needed
3. Write tests in `tests/`
4. Update relevant documentation in `docs/`
5. Register in the relevant YAML config file

## Swapping the AI Brain

The brain is abstracted behind `BrainInterface`:

```python
from jarvis.core.brain.brain_interface import BrainInterface

class MyCustomBrain(BrainInterface):
    async def think(self, prompt, context=None):
        # call your model
        return "response text"

    async def is_available(self):
        return True

    def get_model_info(self):
        return {"name": "my-custom-model"}

# Register:
from jarvis.core.brain.model_manager import ModelManager
manager = ModelManager(brain=MyCustomBrain())
```
