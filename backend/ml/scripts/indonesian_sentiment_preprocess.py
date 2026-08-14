"""
Preprocessing module for Indonesian News Sentiment dataset.

Dataset: intanm/indonesian-financial-sentiment-analysis
Source : Hugging Face Hub
License: Unknown (Publicly available academic/research dataset)
Domain : Indonesian Financial News Headlines
Label origin: Human Annotated

Labels (Original -> Normalized):
  0 -> Negative
  1 -> Neutral
  2 -> Positive

Usage:
    from ml.scripts.indonesian_sentiment_preprocess import load_and_clean
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

DATASET_ID = "intanm/indonesian-financial-sentiment-analysis"
DATASET_SOURCE = "Hugging Face Hub"
DATASET_LICENSE = "Unknown (Academic/Research)"
DATASET_DOMAIN = "Indonesian Financial News Headlines"
LABEL_ORIGIN = "Human Annotated"

LABEL_MAPPING = {
    0: "Negative",
    1: "Neutral",
    2: "Positive"
}
CLASSES = ["Negative", "Neutral", "Positive"]

TEXT_COLUMN = "text"
LABEL_COLUMN = "label"

# ---------------------------------------------------------------------------
# Text cleaning — specialized for sentiment
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Minimal cleaning for Indonesian sentiment text.
    
    CRITICAL: MUST preserve negations (tidak, bukan, belum, jangan, tanpa, kurang, etc.)
    
    Removes:
    - HTML tags and entities
    - Malformed Unicode control chars
    - Redundant whitespace
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&amp;", " ", text)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def load_indonesian_sentiment_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download and return (train_raw, test_raw) DataFrames from Hugging Face."""
    from datasets import load_dataset
    print(f"Downloading: {DATASET_ID} ...")
    ds = load_dataset(DATASET_ID)
    train_df = ds["train"].to_pandas()
    test_df = ds["test"].to_pandas()
    print(f"  Raw train rows: {len(train_df):,}")
    print(f"  Raw test rows : {len(test_df):,}")
    return train_df, test_df


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full preprocessing pipeline.
    Steps:
    1. Clean text (preserve negations)
    2. Map integer labels to string categories (Negative/Neutral/Positive)
    3. Drop missing/invalid labels
    4. Drop empty texts
    5. Remove exact duplicates
    """
    df = df.copy()

    # 1. Clean text
    df[TEXT_COLUMN] = df[TEXT_COLUMN].apply(clean_text)

    # 2. Map labels
    df[LABEL_COLUMN] = df[LABEL_COLUMN].map(LABEL_MAPPING)

    # 3. Drop invalid labels
    before = len(df)
    df = df.dropna(subset=[LABEL_COLUMN])
    df = df[df[LABEL_COLUMN].isin(CLASSES)]
    if len(df) < before:
        print(f"  Dropped {before - len(df)} invalid/missing labels")

    # 4. Drop empty texts
    before = len(df)
    df = df[df[TEXT_COLUMN].str.len() >= 5]
    if len(df) < before:
        print(f"  Dropped {before - len(df)} rows with empty/short text")

    # 5. Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=[TEXT_COLUMN])
    if len(df) < before:
        print(f"  Dropped {before - len(df)} exact duplicates")

    df = df.reset_index(drop=True)
    return df[[TEXT_COLUMN, LABEL_COLUMN]]


def load_and_clean() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: download -> preprocess.
    Returns (train_df, test_df) mapped to Positive/Neutral/Negative.
    """
    train_raw, test_raw = load_indonesian_sentiment_raw()
    
    print("\nPreprocessing train split...")
    train_df = preprocess_df(train_raw)
    print(f"  Final train rows: {len(train_df):,}")
    
    print("\nPreprocessing test split...")
    test_df = preprocess_df(test_raw)
    print(f"  Final test rows : {len(test_df):,}")
    
    print(f"\nClass distribution (Train):")
    print(train_df[LABEL_COLUMN].value_counts().to_string())
    
    return train_df, test_df


if __name__ == "__main__":
    train_df, _ = load_and_clean()
    print(f"\nSample texts (Train):")
    for _, row in train_df.head(5).iterrows():
        print(f"  [{row[LABEL_COLUMN]:<8}] {row[TEXT_COLUMN][:100]}")
