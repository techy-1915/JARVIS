"""Intelligent routing of prompts to appropriate AI models."""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Keywords for routing
CODE_KEYWORDS = [
    "code", "program", "function", "debug", "error", "implementation",
    "python", "javascript", "java", "c++", "rust", "golang",
    "api", "algorithm", "bug", "compile", "syntax", "refactor",
    "class", "method", "variable", "import", "package",
]

REASONING_KEYWORDS = [
    "analyze", "reasoning", "logic", "plan", "strategy", "why",
    "explain", "compare", "evaluate", "assess", "decide",
    "pros and cons", "trade-offs", "approach", "consider",
]


def classify_prompt(prompt: str) -> str:
    """Classify a prompt to determine which model should handle it.

    Args:
        prompt: User input text

    Returns:
        Model identifier: "phi3", "deepseek-coder", or "mistral"
    """
    prompt_lower = prompt.lower()

    # Check for code-related requests
    code_score = sum(1 for kw in CODE_KEYWORDS if kw in prompt_lower)

    # Check for reasoning-related requests
    reasoning_score = sum(1 for kw in REASONING_KEYWORDS if kw in prompt_lower)

    # Check for code patterns (backticks, file extensions, etc.)
    has_code_block = "```" in prompt or bool(
        re.search(r"\.(py|js|java|cpp|rs|go|c|h)$", prompt)
    )

    # Routing logic
    if code_score >= 2 or has_code_block:
        logger.info("Routing → deepseek-coder (code_score=%d)", code_score)
        return "deepseek-coder"
    elif reasoning_score >= 2:
        logger.info("Routing → mistral (reasoning_score=%d)", reasoning_score)
        return "mistral"
    else:
        logger.info("Routing → phi3 (general chat)")
        return "phi3"


def get_system_prompt(model_type: str) -> str:
    """Get appropriate system prompt for the model.

    Args:
        model_type: One of "phi3", "deepseek-coder", "mistral".

    Returns:
        System prompt string.
    """
    prompts = {
        "phi3": (
            "You are JARVIS, a helpful AI assistant. Respond naturally and "
            "conversationally. Format code in markdown code blocks when relevant."
        ),
        "deepseek-coder": (
            "You are JARVIS, an expert programming assistant. Provide clear code "
            "examples, explain your solutions, and format all code in markdown "
            "blocks with language tags."
        ),
        "mistral": (
            "You are JARVIS, an analytical AI assistant. Provide thorough "
            "reasoning, consider multiple perspectives, and structure your "
            "analysis clearly."
        ),
    }
    return prompts.get(model_type, prompts["phi3"])
