"""
Inspect top Indonesian news dataset candidates from Hugging Face.
"""
import io, sys, json
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

CANDIDATES = [
    "fahadh4ilyas/indonesian_news_datasets",
    "SEACrowd/indonesian_news_dataset",
    "iqballx/indonesian_news_datasets",
]

for ds_id in CANDIDATES:
    print(f"\n{'='*60}")
    print(f"  {ds_id}")
    print(f"{'='*60}")
    try:
        r = requests.get(f"https://huggingface.co/api/datasets/{ds_id}", timeout=15)
        info = r.json()
        print(f"  Downloads  : {info.get('downloads', 'N/A')}")
        print(f"  Likes      : {info.get('likes', 'N/A')}")
        print(f"  Tags       : {info.get('tags', [])}")
        card = info.get("cardData", {})
        print(f"  License    : {card.get('license', 'NOT SPECIFIED')}")
        print(f"  Language   : {card.get('language', 'N/A')}")
        # Card README excerpt
        readme_r = requests.get(
            f"https://huggingface.co/datasets/{ds_id}/raw/main/README.md",
            timeout=15
        )
        if readme_r.status_code == 200:
            readme = readme_r.text[:2000]
            print(f"\n  README excerpt:\n{readme[:800]}")
    except Exception as e:
        print(f"  Error: {e}")
