#!/usr/bin/env python3
"""Deploy a LoRA adapter to Ollama as a new model variant.

Usage::

    python scripts/deploy_to_ollama.py --adapter models/lora_adapters/jarvis_v1/final
    python scripts/deploy_to_ollama.py --adapter models/lora_adapters/jarvis_v1/final --base llama3.1:8b --name jarvis_v1
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main(adapter_path: str, base_model: str, model_name: str) -> None:
    """Create an Ollama model from a LoRA adapter."""
    path = Path(adapter_path)
    if not path.exists():
        logger.error("Adapter path does not exist: %s", adapter_path)
        sys.exit(1)

    modelfile_content = (
        f"FROM {base_model}\n"
        f"# LoRA adapter: {adapter_path}\n"
        f'SYSTEM "You are JARVIS, an intelligent AI assistant."\n'
    )
    modelfile_path = path / "Modelfile"
    modelfile_path.write_text(modelfile_content)

    logger.info("Creating Ollama model '%s' from %s ...", model_name, adapter_path)

    proc = await asyncio.create_subprocess_exec(
        "ollama",
        "create",
        model_name,
        "-f",
        str(modelfile_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info("✅ Created Ollama model: %s", model_name)
        print(f"\n✅ Ollama model '{model_name}' created successfully!")
        print(f"   Run with: ollama run {model_name}")
    else:
        err = stderr.decode(errors="replace")
        logger.error("❌ Failed to create Ollama model:\n%s", err)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy LoRA adapter to Ollama")
    parser.add_argument("--adapter", required=True, help="Path to the saved adapter directory")
    parser.add_argument(
        "--base", default="llama3.1:8b", help="Base Ollama model name (default: llama3.1:8b)"
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Name for the new Ollama model (default: derived from adapter path)",
    )
    args = parser.parse_args()

    resolved_name = args.name or f"jarvis_{Path(args.adapter).parent.name}"
    asyncio.run(main(args.adapter, args.base, resolved_name))
