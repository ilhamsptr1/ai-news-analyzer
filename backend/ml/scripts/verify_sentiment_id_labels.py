"""
Verify label mapping for intanm/indonesian-financial-sentiment-analysis
"""
import io, sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datasets import load_dataset

ds = load_dataset("intanm/indonesian-financial-sentiment-analysis")
df = ds["train"].to_pandas()

for label in sorted(df['label'].unique()):
    sample = df[df['label'] == label]['text'].iloc[0]
    print(f"Label {label}: {sample}")
