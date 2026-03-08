"""AI Router package – priority-based AI provider routing with automatic fallback."""

from .router import AIRouter
from .task_classifier import TaskClassifier, TaskType

__all__ = ["AIRouter", "TaskClassifier", "TaskType"]
