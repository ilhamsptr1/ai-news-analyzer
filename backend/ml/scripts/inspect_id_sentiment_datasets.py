"""
Inspect Indonesian Sentiment Dataset candidates.
"""
import io, sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datasets import load_dataset
import pandas as pd

CANDIDATES = [
    {"id": "indonlp/indonlu", "config": "smsa", "name": "IndoNLU (SmSA) - General Reviews"},
    {"id": "intanm/indonesian-financial-sentiment-analysis", "config": None, "name": "Indonesian Financial Sentiment - News"},
    {"id": "indonlp/NusaX-senti", "config": "ind", "name": "NusaX-senti (Indonesian)"},
]

for c in CANDIDATES:
    print(f"\n{'='*60}")
    print(f"CANDIDATE: {c['name']} ({c['id']})")
    print(f"{'='*60}")
    try:
        if c['config']:
            ds = load_dataset(c['id'], c['config'])
        else:
            ds = load_dataset(c['id'])
        
        print(f"Splits: {list(ds.keys())}")
        if "train" in ds:
            df = ds["train"].to_pandas()
            print(f"Train Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Find label column
            label_col = "label" if "label" in df.columns else None
            if not label_col:
                for col in df.columns:
                    if df[col].nunique() <= 5:
                        label_col = col
                        break
                        
            if label_col:
                print(f"Label dist:\n{df[label_col].value_counts().to_string()}")
            else:
                print("Label column not clearly found.")
                
            # Print sample
            text_col = "text" if "text" in df.columns else df.columns[0]
            print(f"\nSample text (idx 0):\n{df[text_col].iloc[0][:150]}")
    except Exception as e:
        print(f"Load failed: {e}")
