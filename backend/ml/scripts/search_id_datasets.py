"""
Search and compare Indonesian news datasets on Hugging Face.
"""
import io, sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests, json

def search_hf(query):
    r = requests.get(
        "https://huggingface.co/api/datasets",
        params={"search": query, "sort": "downloads", "direction": "-1", "limit": 8},
        timeout=15
    )
    return r.json()

candidates = {}

for q in ["indonesian news classification", "berita indonesia kategori", "indonesian news dataset"]:
    results = search_hf(q)
    for d in results:
        did = d.get("id","")
        if did and did not in candidates:
            candidates[did] = d

print(f"Found {len(candidates)} unique candidates:\n")
for did in list(candidates.keys())[:20]:
    print(f"  {did}")
