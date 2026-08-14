"""
Dataset search helper
"""
import requests
import json

r = requests.get("https://huggingface.co/api/datasets?search=financial_phrasebank&sort=downloads&direction=-1")
datasets = r.json()
for d in datasets[:5]:
    print(d["id"])
