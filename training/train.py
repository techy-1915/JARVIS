"""Training orchestrator – runs the full JARVIS training pipeline.

Usage:
    python training/train.py [--config training/config.yaml]

The pipeline:
1. Loads configuration from config.yaml
2. Processes and cleans raw datasets
3. Exports cleaned datasets to the export directory
4. (Optional) Launches fine-tuning when ML deps are available
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.dataset_processor import process as process_datasets  # noqa: E402
from training.fine_tune import fine_tune, load_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(config_path: str = "training/config.yaml", skip_training: bool = False) -> None:
    """Execute the full training pipeline.

    Args:
        config_path: Path to the YAML configuration file.
        skip_training: When True, only process datasets (no fine-tuning).
    """
    cfg = load_config(config_path)
    dataset_cfg = cfg.get("dataset", {})
    export_cfg = cfg.get("export", {})

    dataset_dir = dataset_cfg.get("base_dir", "datasets")
    output_dir = export_cfg.get("output_dir", "datasets/export")
    fmt = export_cfg.get("default_format", "alpaca")

    logger.info("=== Step 1: Processing datasets ===")
    process_datasets(dataset_dir=dataset_dir, output_dir=output_dir, fmt=fmt)

    if not skip_training:
        logger.info("=== Step 2: Fine-tuning ===")
        fine_tune(cfg)
    else:
        logger.info("Skipping fine-tuning (--skip-training flag set)")

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run JARVIS training pipeline")
    parser.add_argument("--config", default="training/config.yaml")
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Only process datasets; skip fine-tuning",
    )
    args = parser.parse_args()
    run_pipeline(config_path=args.config, skip_training=args.skip_training)
