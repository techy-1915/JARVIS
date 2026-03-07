#!/usr/bin/env python3
"""Fine-tune Jarvis using LoRA/QLoRA.

Usage::

    python training/fine_tune_lora.py --dataset training/datasets/example_dataset.jsonl
    python training/fine_tune_lora.py --dataset data.jsonl --config training/config/lora_config.yaml --output-name jarvis_v2
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports (graceful fallback when not installed)
# ---------------------------------------------------------------------------

_TORCH_AVAILABLE = False
_HF_AVAILABLE = False

try:
    import torch  # noqa: F401

    _TORCH_AVAILABLE = True
except ImportError:
    pass

try:
    from datasets import Dataset, load_dataset  # noqa: F401
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # noqa: F401
    from transformers import (  # noqa: F401
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer  # noqa: F401

    _HF_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def load_config(config_path: str = "training/config/lora_config.yaml") -> Dict[str, Any]:
    """Load training configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Parsed config dict.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with path.open() as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------


def load_training_dataset(dataset_path: str, tokenizer: Any) -> Any:
    """Load a JSONL dataset and format examples for SFT training.

    Args:
        dataset_path: Path to the ``.jsonl`` training file.
        tokenizer: HuggingFace tokenizer (used for chat template if available).

    Returns:
        HuggingFace ``Dataset`` with a ``"text"`` column.
    """
    if not _HF_AVAILABLE:
        raise ImportError("datasets package is required. Install with: pip install datasets")

    from datasets import load_dataset

    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def format_instruction(example: Dict[str, Any]) -> Dict[str, Any]:
        if example.get("input"):
            text = (
                f"### Instruction:\n{example['instruction']}\n\n"
                f"### Input:\n{example['input']}\n\n"
                f"### Response:\n{example['output']}"
            )
        else:
            text = (
                f"### Instruction:\n{example['instruction']}\n\n"
                f"### Response:\n{example['output']}"
            )
        return {"text": text}

    return dataset.map(format_instruction)


# ---------------------------------------------------------------------------
# Model preparation
# ---------------------------------------------------------------------------


def prepare_model_for_training(
    model_name: str, config: Dict[str, Any]
) -> Tuple[Any, Any]:
    """Load model and tokenizer with optional 4-bit quantisation.

    Args:
        model_name: HuggingFace model ID or local path.
        config: Parsed training config dict.

    Returns:
        Tuple of ``(model, tokenizer)``.
    """
    if not _HF_AVAILABLE:
        raise ImportError(
            "transformers/peft packages required. Install with: pip install transformers peft"
        )

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model_cfg = config.get("model", {})
    load_in_4bit = model_cfg.get("load_in_4bit", False)

    if load_in_4bit and _TORCH_AVAILABLE:
        import torch

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type=model_cfg.get("bnb_4bit_quant_type", "nf4"),
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
        )

    model.config.use_cache = False
    return model, tokenizer


def setup_lora(model: Any, config: Dict[str, Any]) -> Any:
    """Attach LoRA adapters to *model*.

    Args:
        model: Pre-loaded (optionally quantised) model.
        config: Parsed training config dict.

    Returns:
        Model with LoRA adapters added.
    """
    if not _HF_AVAILABLE:
        raise ImportError("peft package is required. Install with: pip install peft")

    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    model = prepare_model_for_kbit_training(model)

    lora_cfg = config.get("lora", {})
    lora_config = LoraConfig(
        r=lora_cfg.get("r", 16),
        lora_alpha=lora_cfg.get("lora_alpha", 32),
        lora_dropout=lora_cfg.get("lora_dropout", 0.05),
        target_modules=lora_cfg.get("target_modules", ["q_proj", "v_proj"]),
        bias=lora_cfg.get("bias", "none"),
        task_type=lora_cfg.get("task_type", "CAUSAL_LM"),
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def train_model(
    model: Any,
    dataset: Any,
    config: Dict[str, Any],
    output_dir: str,
    tokenizer: Any,
) -> Any:
    """Run SFT training.

    Args:
        model: LoRA-augmented model.
        dataset: Prepared HuggingFace Dataset.
        config: Parsed training config dict.
        output_dir: Directory for checkpoints and final adapter.
        tokenizer: Matching tokenizer.

    Returns:
        Trained SFTTrainer instance.
    """
    if not _HF_AVAILABLE:
        raise ImportError("trl/transformers packages required.")

    from transformers import TrainingArguments
    from trl import SFTTrainer

    training_cfg = config.get("training", {})

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=training_cfg.get("batch_size", 4),
        gradient_accumulation_steps=training_cfg.get("gradient_accumulation_steps", 4),
        learning_rate=training_cfg.get("learning_rate", 2e-4),
        num_train_epochs=training_cfg.get("num_epochs", 3),
        warmup_steps=training_cfg.get("warmup_steps", 100),
        logging_steps=training_cfg.get("logging_steps", 10),
        save_steps=training_cfg.get("save_steps", 500),
        evaluation_strategy="no",  # eval dataset optional
        fp16=_TORCH_AVAILABLE,
        optim="paged_adamw_8bit",
        save_total_limit=3,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        max_seq_length=training_cfg.get("max_seq_length", 2048),
        dataset_text_field="text",
    )

    trainer.train()
    return trainer


def save_adapter(model: Any, output_path: str) -> str:
    """Save the LoRA adapter weights to *output_path*.

    Args:
        model: Trained PEFT model.
        output_path: Target directory.

    Returns:
        The resolved absolute path string.
    """
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(path))
    logger.info("Adapter saved to %s", path)
    return str(path.resolve())


def evaluate_model(model: Any, test_dataset: Any, tokenizer: Any) -> Dict[str, float]:
    """Run basic evaluation on *test_dataset*.

    Args:
        model: Trained model.
        test_dataset: HuggingFace Dataset with a ``"text"`` column.
        tokenizer: Matching tokenizer.

    Returns:
        Dict with at minimum a ``"perplexity"`` key.
    """
    if not _HF_AVAILABLE or not _TORCH_AVAILABLE:
        logger.warning("Evaluation skipped – torch/transformers not available")
        return {"perplexity": float("inf")}

    import math

    import torch
    from transformers import TrainingArguments
    from trl import SFTTrainer

    eval_args = TrainingArguments(
        output_dir="/tmp/eval_tmp",
        per_device_eval_batch_size=4,
        fp16=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=eval_args,
        eval_dataset=test_dataset,
        tokenizer=tokenizer,
        max_seq_length=512,
        dataset_text_field="text",
    )
    metrics = trainer.evaluate()
    loss = metrics.get("eval_loss", float("inf"))
    return {"loss": loss, "perplexity": math.exp(loss) if loss < 100 else float("inf")}


async def deploy_to_ollama(adapter_path: str, base_model: str = "llama3.1:8b") -> str:
    """Create a new Ollama model from a LoRA adapter.

    Writes a Modelfile and calls ``ollama create``.

    Args:
        adapter_path: Path to the saved adapter directory.
        base_model: Name of the base Ollama model.

    Returns:
        The name of the created Ollama model.
    """
    import asyncio

    model_name = f"jarvis_{Path(adapter_path).name}"
    modelfile_content = (
        f"FROM {base_model}\n"
        f"# LoRA adapter: {adapter_path}\n"
        f'SYSTEM "You are JARVIS, an intelligent AI assistant."\n'
    )
    modelfile_path = Path(adapter_path) / "Modelfile"
    modelfile_path.write_text(modelfile_content)

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
        logger.info("Created Ollama model: %s", model_name)
        return model_name
    else:
        err = stderr.decode(errors="replace")
        logger.error("Failed to create Ollama model: %s", err)
        raise RuntimeError(f"ollama create failed: {err}")


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------


def train(
    dataset_path: str,
    config_path: str = "training/config/lora_config.yaml",
    output_name: Optional[str] = None,
) -> str:
    """Run the full LoRA fine-tuning pipeline.

    Args:
        dataset_path: Path to the JSONL training dataset.
        config_path: Path to the YAML config file.
        output_name: Optional suffix for the output adapter directory.

    Returns:
        Absolute path to the saved adapter.

    Raises:
        ImportError: If required ML packages are not installed.
        FileNotFoundError: If the dataset or config file is missing.
    """
    if not _HF_AVAILABLE:
        raise ImportError(
            "Fine-tuning requires: pip install transformers peft trl bitsandbytes accelerate datasets"
        )

    # Load config
    config = load_config(config_path)
    logger.info("Loaded config from %s", config_path)

    # Determine output path
    if output_name is None:
        output_name = f"jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(config["output"]["adapter_path"]) / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare model + tokenizer
    model_name = config["model"]["base_model"]
    logger.info("Loading model: %s", model_name)
    model, tokenizer = prepare_model_for_training(model_name, config)

    # Load dataset
    dataset = load_training_dataset(dataset_path, tokenizer)
    logger.info("Loaded %d training examples", len(dataset))

    # Add LoRA adapters
    model = setup_lora(model, config)

    # Train
    trainer = train_model(model, dataset, config, str(output_dir), tokenizer)

    # Save adapter
    final_path = output_dir / "final"
    adapter_path = save_adapter(trainer.model, str(final_path))

    logger.info("Training complete! Adapter saved to %s", adapter_path)
    # Print machine-readable output for the learning loop to parse
    print(f"ADAPTER_PATH:{adapter_path}")
    return adapter_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Jarvis with LoRA/QLoRA")
    parser.add_argument(
        "--dataset", required=True, help="Path to training dataset (.jsonl)"
    )
    parser.add_argument(
        "--config",
        default="training/config/lora_config.yaml",
        help="Path to LoRA training config YAML",
    )
    parser.add_argument("--output-name", help="Name suffix for output adapter directory")

    args = parser.parse_args()

    try:
        adapter_path = train(
            dataset_path=args.dataset,
            config_path=args.config,
            output_name=args.output_name,
        )
        print(f"\n✅ Training complete!")
        print(f"📦 Adapter saved to: {adapter_path}")
        print(f"\nTo use this adapter with Ollama:")
        print(f"  python scripts/deploy_to_ollama.py --adapter {adapter_path}")
    except ImportError as exc:
        logger.error("Missing dependencies: %s", exc)
        sys.exit(1)
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        sys.exit(1)
