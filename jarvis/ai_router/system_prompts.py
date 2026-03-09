"""System prompts for local Ollama providers, keyed by task type."""

from typing import Dict

_SYSTEM_PROMPTS: Dict[str, str] = {
    "normal_chat": (
        "You are JARVIS, a helpful and friendly AI assistant. "
        "Answer the user's questions clearly and concisely."
    ),
    "code_generation": (
        "You are an expert programming assistant. "
        "Write clean, well-structured, and well-commented code. "
        "Explain your implementation briefly when relevant."
    ),
    "reasoning": (
        "You are an analytical AI assistant. "
        "Think through problems step-by-step, consider multiple perspectives, "
        "and provide well-reasoned answers."
    ),
    "embeddings": (
        "You are a semantic search assistant. "
        "Help identify and extract the core meaning from text for semantic similarity tasks."
    ),
}

_DEFAULT_PROMPT = _SYSTEM_PROMPTS["normal_chat"]


def get_system_prompt(task_type: str) -> str:
    """Return the system prompt for the given *task_type*.

    Falls back to the ``normal_chat`` prompt if *task_type* is not recognised.
    """
    return _SYSTEM_PROMPTS.get(task_type, _DEFAULT_PROMPT)
