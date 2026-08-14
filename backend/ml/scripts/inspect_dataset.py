"""
Dataset Inspection Script -- AG News (from Hugging Face)
Displays summary statistics without performing any training.

Usage:
    python ml/scripts/inspect_dataset.py
"""

import io
import sys

# Force UTF-8 on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

# Ensure backend/ is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

LABEL_MAP = {0: "World", 1: "Sports", 2: "Business", 3: "Technology"}


def load_agnews() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load AG News from Hugging Face datasets library."""
    from datasets import load_dataset
    print("Loading AG News dataset from Hugging Face...")
    ds = load_dataset("fancyzhx/ag_news", trust_remote_code=False)
    train_df = ds["train"].to_pandas()
    test_df = ds["test"].to_pandas()
    # Map integer labels to string categories
    train_df["category"] = train_df["label"].map(LABEL_MAP)
    test_df["category"] = test_df["label"].map(LABEL_MAP)
    return train_df, test_df


def inspect(df: pd.DataFrame, split_name: str) -> None:
    print(f"\n{'='*60}")
    print(f"  SPLIT: {split_name.upper()}")
    print(f"{'='*60}")
    print(f"  Rows:              {len(df):,}")
    print(f"  Columns:           {list(df.columns)}")

    # Missing values
    missing = df.isnull().sum()
    print(f"\n  Missing values:")
    for col, n in missing.items():
        print(f"    {col}: {n}")

    # Duplicates
    dup_text = df["text"].duplicated().sum()
    print(f"\n  Duplicate texts:   {dup_text:,}")

    # Label distribution
    dist = df["category"].value_counts().sort_index()
    print(f"\n  Class Distribution:")
    for cat, count in dist.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"    {cat:<15} {count:>6,}  ({pct:5.1f}%)  {bar}")

    # Text length stats
    df = df.copy()
    df["text_len"] = df["text"].str.split().str.len()
    print(f"\n  Text length (words):")
    print(f"    Min:   {df['text_len'].min()}")
    print(f"    Max:   {df['text_len'].max()}")
    print(f"    Mean:  {df['text_len'].mean():.1f}")
    print(f"    Median:{df['text_len'].median():.1f}")

    # Sample rows
    print(f"\n  Sample rows (first 3):")
    for i, row in df.head(3).iterrows():
        text_preview = row["text"][:120].replace("\n", " ")
        print(f"    [{row['category']}] {text_preview}…")


def main():
    print("\n" + "=" * 60)
    print("  AI NEWS ANALYZER — DATASET INSPECTION")
    print("  Dataset: AG News (fancyzhx/ag_news @ Hugging Face)")
    print("=" * 60)

    print("\nDataset Information:")
    print("-" * 40)
    print("  Name:     AG News")
    print("  Source:   Hugging Face Hub")
    print("  URL:      https://huggingface.co/datasets/fancyzhx/ag_news")
    print("  License:  Unknown / Public use (research & portfolio)")
    print("  Text:     'text' column — title + description combined")
    print("  Labels:   4 integer labels mapped to string categories")
    print()
    print("  Label Mapping (original → normalized):")
    for k, v in LABEL_MAP.items():
        print(f"    {k} → {v}")

    train_df, test_df = load_agnews()

    inspect(train_df, "train")
    inspect(test_df, "test")

    print(f"\n{'='*60}")
    print("  INSPECTION COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
