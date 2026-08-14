"""
Preprocessing module for Financial News Sentiment dataset.

Responsibilities:
  - Load dataset from Hugging Face (zeroshot/twitter-financial-news-sentiment)
  - Map labels (0 -> Negative, 1 -> Positive, 2 -> Neutral)
  - Clean text (normalize whitespace, handle missing, remove URLs)
  - Return clean DataFrames ready for splitting

Usage:
    from ml.scripts.sentiment_preprocess import load_and_clean
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RANDOM_STATE = 42

LABEL_MAP = {
    0: "Negative",  # Bearish
    1: "Positive",  # Bullish
    2: "Neutral"    # Neutral
}

CATEGORIES = ["Negative", "Neutral", "Positive"]

TEXT_COLUMN = "text"
LABEL_COLUMN = "sentiment"


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalize sentiment text.
    Operations:
    - Unicode NFC normalization
    - Remove URLs (important for Twitter/News data)
    - Normalize whitespace
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    text = unicodedata.normalize("NFC", text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', ' ', text)
    
    # Remove HTML entities
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Load & clean
# ---------------------------------------------------------------------------

def load_sentiment_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    from datasets import load_dataset
    print("Downloading Sentiment dataset from Hugging Face...")
    ds = load_dataset("zeroshot/twitter-financial-news-sentiment")
    train_raw = ds["train"].to_pandas()
    # The dataset has 'train' and 'validation' splits natively
    val_raw = ds["validation"].to_pandas()
    return train_raw, val_raw


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Map labels
    df[LABEL_COLUMN] = df["label"].map(LABEL_MAP)

    # Clean text
    df[TEXT_COLUMN] = df[TEXT_COLUMN].apply(clean_text)

    # Drop missing values
    before = len(df)
    df = df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])
    df = df[df[TEXT_COLUMN].str.len() > 5]  # Remove near-empty texts
    after_missing = len(df)
    if before != after_missing:
        print(f"  Dropped {before - after_missing} rows with missing/empty text")

    # Drop duplicates
    before_dup = len(df)
    df = df.drop_duplicates(subset=[TEXT_COLUMN])
    after_dup = len(df)
    if before_dup != after_dup:
        print(f"  Dropped {before_dup - after_dup} duplicate texts")

    df = df.reset_index(drop=True)

    return df[[TEXT_COLUMN, LABEL_COLUMN]]


def load_and_clean() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: download -> preprocess.
    Returns:
        (train_df, val_df) -- cleaned, columns: [text, sentiment]
    """
    train_raw, val_raw = load_sentiment_raw()

    print("Preprocessing train split...")
    train_df = preprocess_df(train_raw)
    print(f"  Train rows after cleaning: {len(train_df):,}")

    print("Preprocessing validation split...")
    val_df = preprocess_df(val_raw)
    print(f"  Validation rows after cleaning:  {len(val_df):,}")

    return train_df, val_df


if __name__ == "__main__":
    train_df, val_df = load_and_clean()
    print(f"\nTrain sample:\n{train_df.head(3)}")
    print(f"\nClass distribution (train):")
    print(train_df[LABEL_COLUMN].value_counts())
