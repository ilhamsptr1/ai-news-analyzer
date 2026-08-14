"""
Search HF for Indonesian Sentiment Datasets
"""
import io, sys, requests
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def search_hf(query):
    r = requests.get(
        "https://huggingface.co/api/datasets",
        params={"search": query, "sort": "downloads", "direction": "-1", "limit": 10},
        timeout=15
    )
    return r.json()

candidates = {}
queries = ["indonesian sentiment", "sentiment analisis indonesia", "indo sentiment"]
for q in queries:
    for d in search_hf(q):
        did = d.get("id", "")
        if did not in candidates:
            candidates[did] = d

print(f"Found {len(candidates)} unique candidates:\n")
for did, info in list(candidates.items())[:15]:
    tags = info.get("tags", [])
    print(f"  - {did} | Downloads: {info.get('downloads', 0)}")
