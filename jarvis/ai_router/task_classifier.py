"""Task classification for AI routing – maps prompts to task types."""

import logging
import re
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Task type definitions
# ---------------------------------------------------------------------------


class TaskType(str, Enum):
    """Supported task categories for routing."""

    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    NORMAL_CHAT = "normal_chat"
    EMBEDDINGS = "embeddings"


# ---------------------------------------------------------------------------
# Keyword / pattern lists  (re-use and extend existing jarvis.ai.router lists)
# ---------------------------------------------------------------------------

_CODE_KEYWORDS: List[str] = [
    "code", "coding", "program", "script", "snippet", "example code",
    "complete code", "write code", "generate code", "implement", "implementation",
    "build", "develop",
    # constructs
    "function", "class", "method", "variable", "loop", "recursion", "pointer",
    "array", "linked list", "stack", "queue", "tree", "graph", "structure",
    # debugging
    "debug", "bug", "error", "fix", "issue", "crash", "stacktrace", "traceback",
    "segmentation fault", "syntax error", "runtime error", "compile error",
    # software dev
    "algorithm", "data structure", "logic implementation",
    "refactor", "optimize code", "performance", "memory leak",
    # languages
    "python", "javascript", "typescript", "java", "c++", "cpp", "golang",
    "go", "rust", "php", "ruby", "kotlin", "swift", "sql", "bash",
    # ecosystem
    "api", "endpoint", "backend", "frontend", "database",
    "framework", "library", "sdk", "package", "module", "dependency",
    "import", "export", "build system", "compile", "run program",
    "repository", "git", "commit", "branch", "pull request",
    # ML/AI dev
    "vector database", "embedding", "token", "prompt", "llm",
    "transformer", "model inference", "fine tuning", "dataset",
]

_REASONING_KEYWORDS: List[str] = [
    "analyze", "analysis", "reason", "reasoning", "logic", "logical",
    "think", "thought", "consider", "evaluate", "assess",
    "explain", "why", "how", "how does", "how can", "what happens",
    "clarify", "describe", "elaborate", "interpret",
    "compare", "contrast", "difference", "versus", "vs",
    "advantages", "disadvantages", "pros and cons", "trade-offs",
    "decide", "choose", "which is better", "recommend",
    "suggest", "best approach", "best method", "strategy",
    "plan", "planning", "roadmap", "design",
    "architecture", "system design", "workflow", "process",
    "infer", "deduce", "derive", "conclude", "justify",
    "argument", "rationale", "perspective",
    "what if", "scenario", "hypothetical", "prediction",
    "predict", "future outcome", "implication", "consequence",
    "improve", "optimize", "enhance", "better solution",
    "insight", "observation",
]

_CHAT_KEYWORDS: List[str] = [
    "hello", "hi", "hey", "thanks", "thank you",
    "who are you", "what can you do",
    "tell me", "talk about", "conversation",
    "opinion", "thoughts",
]

_EMBEDDING_KEYWORDS: List[str] = [
    "embed", "embedding", "similarity", "semantic search",
    "vector", "encode", "representation",
]

_FORCE_CODE_KEYWORDS: List[str] = [
    "write a program", "write code", "generate code",
    "debug this", "fix this code", "implement this", "complete code",
]

_CODE_PATTERNS: List[str] = [
    r"```",
    r"\bdef\b",
    r"\bclass\b",
    r"\bfunction\b",
    r"\bimport\b",
    r"\breturn\b",
]

_FILE_EXT_PATTERN = re.compile(
    r"\.(py|js|ts|java|cpp|rs|go|c|h|php|rb|kt|swift|sql|sh)\b"
)


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


class TaskClassifier:
    """Classify a prompt into a :class:`TaskType` using keyword heuristics."""

    def classify(self, prompt: str) -> TaskType:
        """Return the most appropriate :class:`TaskType` for *prompt*.

        Args:
            prompt: Raw user input text.

        Returns:
            Best matching :class:`TaskType`.
        """
        prompt_lower = prompt.lower()

        # --- Force-code triggers (explicit code generation requests) ---
        for kw in _FORCE_CODE_KEYWORDS:
            if kw in prompt_lower:
                logger.debug("TaskClassifier → CODE_GENERATION (force kw: %r)", kw)
                return TaskType.CODE_GENERATION

        # --- Embeddings ---
        if any(kw in prompt_lower for kw in _EMBEDDING_KEYWORDS):
            logger.debug("TaskClassifier → EMBEDDINGS")
            return TaskType.EMBEDDINGS

        # --- Scoring ---
        code_score = sum(1 for kw in _CODE_KEYWORDS if kw in prompt_lower)
        reasoning_score = sum(1 for kw in _REASONING_KEYWORDS if kw in prompt_lower)
        chat_score = sum(1 for kw in _CHAT_KEYWORDS if kw in prompt_lower)

        has_code_pattern = any(re.search(p, prompt_lower) for p in _CODE_PATTERNS)
        has_file_ext = bool(_FILE_EXT_PATTERN.search(prompt_lower))

        # --- Routing decision ---
        if code_score >= 2 or has_code_pattern or has_file_ext:
            logger.debug(
                "TaskClassifier → CODE_GENERATION (code_score=%d, pattern=%s)",
                code_score, has_code_pattern,
            )
            return TaskType.CODE_GENERATION

        if reasoning_score >= 2:
            logger.debug(
                "TaskClassifier → REASONING (reasoning_score=%d)", reasoning_score
            )
            return TaskType.REASONING

        if chat_score >= 1:
            logger.debug("TaskClassifier → NORMAL_CHAT (chat keyword matched)")
            return TaskType.NORMAL_CHAT

        logger.debug("TaskClassifier → NORMAL_CHAT (default)")
        return TaskType.NORMAL_CHAT


# Module-level singleton
_classifier: TaskClassifier | None = None


def get_task_classifier() -> TaskClassifier:
    """Return the module-level :class:`TaskClassifier` singleton."""
    global _classifier
    if _classifier is None:
        _classifier = TaskClassifier()
    return _classifier
