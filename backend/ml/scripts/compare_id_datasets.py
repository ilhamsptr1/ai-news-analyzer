"""
Try loading known Indonesian news datasets from HF to compare actual data quality.
"""
import io, sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datasets import load_dataset
import pandas as pd

# ---- Candidate A: fahadh4ilyas/indonesian_news_datasets (LLM labels) ----
print("\n" + "="*60)
print("CANDIDATE A: fahadh4ilyas/indonesian_news_datasets")
print("="*60)
try:
    ds_a = load_dataset("fahadh4ilyas/indonesian_news_datasets")
    print(f"Splits: {list(ds_a.keys())}")
    df_a = ds_a["train"].to_pandas()
    print(f"Shape: {df_a.shape}")
    print(f"Columns: {list(df_a.columns)}")
    print(f"Label dist:\n{df_a['label'].value_counts()}")
    print(f"Missing title: {df_a['title'].isna().sum()}")
    if 'content' in df_a.columns:
        print(f"Missing content: {df_a['content'].isna().sum()}")
    print(f"Duplicates (title): {df_a.duplicated(subset=['title']).sum()}")
    print(f"\nSample (index 0):\n  title: {df_a['title'].iloc[0][:80]}")
    print(f"  label: {df_a['label'].iloc[0]}")
except Exception as e:
    print(f"Load failed: {e}")

# ---- Candidate B: SEACrowd/indonesian_news_dataset ----
print("\n" + "="*60)
print("CANDIDATE B: SEACrowd/indonesian_news_dataset")
print("="*60)
try:
    ds_b = load_dataset("SEACrowd/indonesian_news_dataset", trust_remote_code=True)
    print(f"Splits: {list(ds_b.keys())}")
    df_b_train = ds_b["train"].to_pandas()
    print(f"Train shape: {df_b_train.shape}")
    print(f"Columns: {list(df_b_train.columns)}")
    print(f"Label col: label or topic?")
    # find label column
    for col in df_b_train.columns:
        if df_b_train[col].dtype == object and df_b_train[col].nunique() < 20:
            print(f"  Column '{col}' unique values: {df_b_train[col].unique()[:10]}")
    if "train" in ds_b:
        print(f"Train rows: {len(ds_b['train'])}")
    if "test" in ds_b:
        print(f"Test rows: {len(ds_b['test'])}")
except Exception as e:
    print(f"Load failed: {e}")
