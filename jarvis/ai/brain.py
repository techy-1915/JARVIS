"""Unified AI brain layer for interacting with Ollama models."""

import json
import logging
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiohttp

from .models import DEFAULT_MODEL, MODELS
from .router import classify_prompt, get_system_prompt

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


class AIBrain:
    """Handles AI model interactions with intelligent routing."""

    def __init__(self, ollama_url: str = OLLAMA_BASE_URL) -> None:
        self.ollama_url = ollama_url

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Union[AsyncIterator[str], str]:
        """Generate a response from the AI.

        Args:
            prompt: User input
            model: Specific model to use (auto-routes if None)
            stream: Whether to stream the response
            context: Conversation history

        Returns:
            Response text, or async iterator of text chunks when streaming.
        """
        # Auto-route if no model specified
        if model is None:
            model = classify_prompt(prompt)

        # Get model config
        model_config = MODELS.get(model, MODELS[DEFAULT_MODEL])
        logger.info("Using model: %s", model_config.display_name)

        # Build messages
        messages: List[Dict[str, str]] = []
        if context:
            messages.extend(context)

        # Prepend system prompt
        system_prompt = get_system_prompt(model)
        messages.insert(0, {"role": "system", "content": system_prompt})

        # Append user message
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": model_config.name,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": model_config.temperature,
            },
        }

        if stream:
            return self._generate_stream(payload)
        else:
            return await self._generate_complete(payload)

    async def _generate_complete(self, payload: Dict[str, Any]) -> str:
        """Generate a complete (non-streamed) response."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("Ollama error: %s", error_text)
                        return (
                            "I'm having trouble connecting to my AI brain. "
                            "Please check that Ollama is running."
                        )
                    data = await response.json()
                    return data.get("message", {}).get("content", "")

        except aiohttp.ClientError as exc:
            logger.error("Ollama connection error: %s", exc)
            return (
                "I'm having trouble connecting to my AI brain. "
                "Please ensure Ollama is running on port 11434."
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error: %s", exc)
            return f"An unexpected error occurred: {exc}"

    async def _generate_stream(self, payload: Dict[str, Any]) -> AsyncIterator[str]:
        """Generate a streaming response, yielding text chunks."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk:
                                    content = chunk["message"].get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as exc:  # noqa: BLE001
            logger.error("Streaming error: %s", exc)
            yield f"[Streaming error: {exc}]"

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown text.

        Args:
            text: Markdown text potentially containing fenced code blocks.

        Returns:
            List of dicts with "language" and "code" keys.
        """
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.finditer(pattern, text, re.DOTALL)
        return [
            {"language": m.group(1) or "text", "code": m.group(2).strip()}
            for m in matches
        ]

    async def check_health(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if the Ollama API is reachable.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200
        except Exception:  # noqa: BLE001
            return False
