"""
Preprocessing module for AG News dataset.

Responsibilities:
  - Load AG News from Hugging Face
  - Clean text (normalize whitespace, unicode, handle missing)
  - Remove duplicates
  - Return clean DataFrames ready for splitting

Usage (standalone):
    python ml/scripts/preprocess.py

Usage (import):
    from ml.scripts.preprocess import load_and_clean, LABEL_MAP, CATEGORIES
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# Ensure backend/ on path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RANDOM_STATE = 42

LABEL_MAP = {0: "World", 1: "Sports", 2: "Business", 3: "Technology"}

CATEGORIES = sorted(LABEL_MAP.values())  # ['Business', 'Sports', 'Technology', 'World']

TEXT_COLUMN = "text"
LABEL_COLUMN = "category"


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalize article text for TF-IDF processing.

    Operations:
    - Convert to string
    - Unicode NFC normalization
    - Remove HTML tags
    - Normalize whitespace (collapse multiple spaces/newlines)
    - Strip leading/trailing whitespace

    NOT performed (reserved for Phase 4B+):
    - Stemming
    - Stopword removal
    - Tokenization
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove HTML entities
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Normalize whitespace (newlines, tabs → single space)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Load & clean
# ---------------------------------------------------------------------------

def load_agnews_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download AG News from Hugging Face and return raw DataFrames."""
    from datasets import load_dataset
    print("Downloading AG News from Hugging Face...")
    ds = load_dataset("fancyzhx/ag_news", trust_remote_code=False)
    train_raw = ds["train"].to_pandas()
    test_raw = ds["test"].to_pandas()
    return train_raw, test_raw


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply cleaning pipeline to a DataFrame.

    Steps:
      1. Map integer label → string category
      2. Clean text
      3. Drop rows with empty text or missing label
      4. Drop exact duplicate texts within same category
    """
    df = df.copy()

    # Map labels
    df[LABEL_COLUMN] = df["label"].map(LABEL_MAP)

    # Clean text
    df[TEXT_COLUMN] = df[TEXT_COLUMN].apply(clean_text)

    # Drop missing values
    before = len(df)
    df = df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    df = df[df[TEXT_COLUMN].str.len() > 10]  # Remove near-empty texts
    after_missing = len(df)
    if before != after_missing:
        print(f"  Dropped {before - after_missing} rows with missing/empty text")

    # Drop duplicates (same text, same category)
    before_dup = len(df)
    df = df.drop_duplicates(subset=[TEXT_COLUMN])
    after_dup = len(df)
    if before_dup != after_dup:
        print(f"  Dropped {before_dup - after_dup} duplicate texts")

    # Reset index
    df = df.reset_index(drop=True)

    return df[[TEXT_COLUMN, LABEL_COLUMN]]


def load_and_clean() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: download → preprocess.

    Returns:
        (train_df, test_df) — both cleaned, columns: [text, category]
    """
    train_raw, test_raw = load_agnews_raw()

    print("Preprocessing train split...")
    train_df = preprocess_df(train_raw)
    print(f"  Train rows after cleaning: {len(train_df):,}")

    print("Preprocessing test split...")
    test_df = preprocess_df(test_raw)
    print(f"  Test rows after cleaning:  {len(test_df):,}")

    return train_df, test_df


# ---------------------------------------------------------------------------
# Standalone run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n=== Preprocessing Pipeline ===")
    train_df, test_df = load_and_clean()
    print(f"\nTrain sample:\n{train_df.head(3)}")
    print(f"\nTest sample:\n{test_df.head(3)}")
    print("\nClass distribution (train):")
    print(train_df[LABEL_COLUMN].value_counts())
    print("\nPreprocessing complete.")
