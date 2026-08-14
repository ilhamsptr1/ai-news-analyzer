"""
Inspect Sentiment Dataset
Using `financial_phrasebank` (sentences_50agree) which contains financial news sentences
labeled by 16 people with at least 50% agreement.
"""
import io
import sys
from datasets import load_dataset
import pandas as pd

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def main():
    print("Loading Financial News Sentiment dataset...")
    try:
        ds = load_dataset("zeroshot/twitter-financial-news-sentiment")
        df = ds["train"].to_pandas()
        
        print("\nDataset loaded successfully!")
        print(f"Total Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        print("\nMissing values:")
        print(df.isnull().sum())
        
        print("\nDuplicates:")
        text_col = 'text' if 'text' in df.columns else 'sentence'
        print(f"Duplicate rows: {df.duplicated(subset=[text_col]).sum()}")
        
        print("\nLabel distribution:")
        print(df['label'].value_counts())
        
        print("\nSample Data:")
        for idx, row in df.head(5).iterrows():
            print(f"[{row['label']}] {row[text_col]}")
            
    except Exception as e:
        print(f"Failed to load: {e}")

if __name__ == "__main__":
    main()
