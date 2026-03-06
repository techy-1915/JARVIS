"""Dataset processor – clean and prepare raw interaction logs for training."""

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running from the repo root: python training/dataset_processor.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis.core.learning.dataset_builder import DatasetBuilder  # noqa: E402
from jarvis.core.learning.learning_engine import LearningEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def process(dataset_dir: str = "datasets", output_dir: str = "datasets/export", fmt: str = "alpaca") -> None:
    """Load raw logs, clean them, and export cleaned datasets.

    Args:
        dataset_dir: Root directory containing raw JSONL interaction logs.
        output_dir: Directory where cleaned datasets will be written.
        fmt: Output format (``"alpaca"`` or ``"chatml"``).
    """
    engine = LearningEngine(dataset_dir=dataset_dir)
    builder = DatasetBuilder(engine)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    stats = engine.get_dataset_stats()
    logger.info("Raw dataset stats: %s", stats)

    for category in ("conversations", "coding", "reasoning"):
        raw = engine.build_dataset(category)
        cleaned = builder.clean_dataset(raw)
        logger.info("Category '%s': %d raw → %d cleaned", category, len(raw), len(cleaned))

        out_file = out_path / f"{category}_{fmt}.json"
        with out_file.open("w") as fh:
            json.dump(cleaned, fh, indent=2)
        logger.info("Saved → %s", out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JARVIS interaction datasets")
    parser.add_argument("--dataset-dir", default="datasets", help="Raw dataset directory")
    parser.add_argument("--output-dir", default="datasets/export", help="Output directory")
    parser.add_argument("--format", choices=["alpaca", "chatml"], default="alpaca", dest="fmt")
    args = parser.parse_args()
    process(dataset_dir=args.dataset_dir, output_dir=args.output_dir, fmt=args.fmt)
