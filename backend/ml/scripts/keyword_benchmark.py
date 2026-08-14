import sys
sys.path.insert(0, ".")
from app.ai.keyword_extractor import KeywordExtractor

ext = KeywordExtractor()

text = (
    "Apple announced a new artificial intelligence chip for its iPhone devices. "
    "The machine learning processor will power Siri and on-device AI models. "
    "CEO Tim Cook said the technology will revolutionize the smartphone industry. "
    "The chip is manufactured by TSMC using a 3nm process."
)

result = ext.extract(text, top_n=8)
print("Method:", result["method"])
print("Keywords:")
for k in result["keywords"]:
    print(f"  [score={k['score']:.4f}] {k['keyword']}")

print("\nBenchmark - YAKE vs TF-IDF:")
import time

from app.ai.tfidf_keyword_extractor import TfidfKeywordExtractor

long_text = text * 20  # simulate longer article

start = time.time()
yake_result = ext.extract(long_text, top_n=10)
yake_time = time.time() - start

start = time.time()
tfidf_ext = TfidfKeywordExtractor()
tfidf_result = tfidf_ext.extract(long_text, top_n=10)
tfidf_time = time.time() - start

print(f"  YAKE time : {yake_time:.3f}s  | keywords: {len(yake_result['keywords'])}")
print(f"  TF-IDF time: {tfidf_time:.3f}s  | keywords: {len(tfidf_result)}")
print("\nYAKE top keywords:")
for k in yake_result["keywords"][:5]:
    print(f"  {k['keyword']}")
print("\nTF-IDF top keywords:")
for k in tfidf_result[:5]:
    print(f"  {k['keyword']}")
