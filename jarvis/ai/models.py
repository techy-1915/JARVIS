"""Model configurations for Ollama-based AI models."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModelConfig:
    """Configuration for an Ollama model."""

    name: str
    display_name: str
    context_window: int
    capabilities: List[str]
    temperature: float = 0.7


MODELS: Dict[str, ModelConfig] = {
    "phi3": ModelConfig(
        name="phi3",
        display_name="Phi-3 (General Chat)",
        context_window=4096,
        capabilities=["chat", "general", "fast"],
        temperature=0.7,
    ),
    "deepseek-coder": ModelConfig(
        name="deepseek-coder:6.7b",
        display_name="DeepSeek Coder (Programming)",
        context_window=16384,
        capabilities=["code", "programming", "debug"],
        temperature=0.3,
    ),
    "mistral": ModelConfig(
        name="mistral",
        display_name="Mistral (Reasoning)",
        context_window=8192,
        capabilities=["reasoning", "planning", "analysis"],
        temperature=0.5,
    ),
    "fallback": ModelConfig(
        name="llama3.1:8b",
        display_name="Llama 3.1 (Fallback)",
        context_window=8192,
        capabilities=["general"],
        temperature=0.7,
    ),
}

DEFAULT_MODEL = "phi3"
