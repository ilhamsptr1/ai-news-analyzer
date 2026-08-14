# AI News Analyzer — Machine Learning (Phase 4A)

## Overview

Phase 4A implements a **news category classification pipeline** using classical NLP/ML techniques. The model reads article text and predicts one of 4 news categories.

---

## Dataset

| Field       | Value |
|-------------|-------|
| **Name**    | AG News |
| **Source**  | Hugging Face Hub |
| **URL**     | https://huggingface.co/datasets/fancyzhx/ag_news |
| **License** | Unknown / Public use for research and portfolio projects |
| **Total**   | 127,600 samples (120,000 train + 7,600 test) |
| **Columns** | `text` (headline + body), `label` (integer) |

### Label Mapping (original → normalized)

| Original Label | Normalized Category |
|---------------|---------------------|
| 0 | World |
| 1 | Sports |
| 2 | Business |
| 3 | Technology |

**Note:** The AG News dataset provides 4 categories. The remaining target categories (Politics, Entertainment, Science, Health) were not available in this dataset. They will be added in a future phase when a multi-category dataset is integrated.

---

## Directory Structure

```
backend/ml/
├── data/
│   ├── raw/           # Downloaded datasets (gitignored — too large)
│   └── processed/     # Cleaned/cached data (gitignored)
├── evaluation/
│   ├── classification_report.txt           # Final test set results
│   ├── classification_report_*_val.txt     # Validation results per model
│   └── confusion_matrix.png                # Best model confusion matrix
├── models/
│   ├── news_category_model.joblib          # Saved sklearn Pipeline
│   └── model_metadata.json                 # Training metadata + metrics
├── notebooks/                              # Jupyter notebooks (future)
├── scripts/
│   ├── __init__.py
│   ├── inspect_dataset.py                  # Dataset inspection (no training)
│   ├── preprocess.py                       # Preprocessing module
│   └── train_classifier.py                 # Training pipeline
├── __init__.py
└── README.md
```

---

## How to Run

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Inspect dataset (no training)

```bash
python ml/scripts/inspect_dataset.py
```

### 3. Train the classifier

```bash
python ml/scripts/train_classifier.py
```

This will:
- Download AG News from Hugging Face (~30 MB)
- Preprocess and split data
- Train 3 models (Naive Bayes, Logistic Regression, Linear SVM)
- Evaluate on validation + test sets
- Save the best model to `ml/models/news_category_model.joblib`
- Save evaluation artifacts to `ml/evaluation/`

---

## Models Compared

| Model | Description |
|-------|-------------|
| **Multinomial Naive Bayes** | Baseline — fast, interpretable, works well with TF-IDF |
| **Logistic Regression** | Strong baseline with `predict_proba` support |
| **Linear SVM (Calibrated)** | Often best for text classification; calibrated for probabilities |

### TF-IDF Parameters

```python
TfidfVectorizer(
    ngram_range=(1, 2),    # unigrams + bigrams
    min_df=2,              # ignore very rare terms
    max_df=0.95,           # ignore near-universal terms
    sublinear_tf=True,     # log(tf) scaling
    max_features=100_000,  # vocabulary cap
)
```

### Data Split

```
AG News native split:
  Train (original): 120,000
  → Split into:
      Train:      102,000 (85%)
      Validation:  18,000 (15%)
  Test (native):    7,600 (separate, untouched)

stratify=y applied to maintain class balance.
```

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Accuracy** | Overall correct predictions / total |
| **Precision** | TP / (TP + FP) per class |
| **Recall** | TP / (TP + FN) per class |
| **F1-score** | Harmonic mean of Precision and Recall |
| **Macro F1** | Unweighted mean of per-class F1 (primary metric) |
| **Weighted F1** | Class-count-weighted F1 |

**Primary selection criterion: Macro F1** — ensures all classes are treated equally regardless of size.

---

## Model Artifacts

| File | Description |
|------|-------------|
| `models/news_category_model.joblib` | Full sklearn Pipeline (TF-IDF + Classifier) |
| `models/model_metadata.json` | Dataset info, metrics, parameters, training date |
| `evaluation/classification_report.txt` | Full classification report (test set) |
| `evaluation/confusion_matrix.png` | Confusion matrix visualization |

---

## Inference

The model is used by the backend via:

```python
from app.ai.category_classifier import get_classifier

clf = get_classifier()
result = clf.predict("Apple announced a new AI chip for iPhone...")
# → {"category": "Technology", "confidence": 0.94, "all_scores": {...}}
```

The model is loaded **lazily** — only on first call. It is cached for the lifetime of the process.

---

## Reproducibility

| Setting | Value |
|---------|-------|
| `RANDOM_STATE` | 42 |
| Train/val split | 85% / 15% stratified |
| Test set | AG News native test (7,600 samples, never seen during training) |
| TF-IDF fit | Training data only (no leakage to val/test) |

---

## Important Notes

- No data leakage: TF-IDF is fitted **only on training data**, then `transform`-only on val/test.
- Confidence scores are real probabilities: Naive Bayes and Logistic Regression use `predict_proba`. Linear SVM uses `CalibratedClassifierCV` (isotonic regression calibration).
- All reported metrics come from the **native test set** that was never used during training or model selection.

---

## Phase 4B-1: Sentiment Analysis

The sentiment analysis model predicts whether an article or text snippet is `Positive`, `Neutral`, or `Negative`.

### Dataset
- **Name:** Twitter Financial News Sentiment
- **Source:** Hugging Face Hub (`zeroshot/twitter-financial-news-sentiment`)
- **License:** Unknown / Public use for research
- **Total:** 11,931 samples (9,543 train + 2,388 validation)
- **Labels:**
  - 0 → Negative (Bearish)
  - 1 → Positive (Bullish)
  - 2 → Neutral

### Preprocessing
- Removed URLs (`http/https`) to prevent noise.
- Handled HTML entities and whitespace.
- Applied Stratified Split (85/15) on the training set, keeping the native validation set strictly for Final Testing.

### Model Comparison & Best Model
Trained using `TF-IDF` + Classical ML:
1. Multinomial Naive Bayes (Macro F1: ~74%)
2. Logistic Regression (Macro F1: ~73%)
3. **Linear SVM (Calibrated) (Macro F1: ~76%) ← BEST MODEL**

### Final Test Set Performance
- **Test Accuracy:** 83.35%
- **Macro F1:** 76.11%
- Target of >=80% Accuracy and >=75% Macro F1 was successfully met.

### Artifacts
- Model: `models/sentiment_model.joblib`
- Metadata: `models/sentiment_model_metadata.json`
- Inference Class: `app.ai.sentiment_classifier.SentimentClassifier`

### Inference Usage
```python
from app.ai.sentiment_classifier import get_sentiment_classifier

clf = get_sentiment_classifier()
result = clf.predict("The company reported a massive profit increase.")
# -> {"sentiment": "Positive", "confidence": 0.85, "all_scores": {...}}
```

---

## Phase 4B-2: Keyword Extraction

Extracts keywords and keyphrases from article text using unsupervised NLP algorithms.

### Algorithm

**Primary: YAKE (Yet Another Keyword Extractor)**

- Library: `yake>=0.4.8`
- No training dataset required — fully unsupervised
- Handles multi-word keyphrases (unigrams, bigrams, trigrams)
- CPU-friendly and fast (~24ms for a 200-word article)
- Language: English (`lan="en"`)

**Fallback: TF-IDF**

- Used automatically if YAKE raises an exception
- Fits on the single input document (not pre-trained)
- Produces n-gram keywords (ngram_range=(1,3))

### Training

No training dataset. Both YAKE and TF-IDF are fully unsupervised.

### Score Interpretation

| Algorithm | Score Semantics |
|-----------|----------------|
| YAKE      | **Lower = more relevant** (sorted ascending) |
| TF-IDF    | **Higher = more relevant** (sorted descending) |

> ⚠️ YAKE scores are statistical relevance scores, **NOT probabilities or confidence values**.

### Language

English. Configurable via `_YAKE_LANGUAGE` constant in `keyword_extractor.py`.

### Modules

| File | Description |
|------|-------------|
| `app/ai/keyword_extractor.py` | Primary extractor (YAKE + fallback logic) |
| `app/ai/tfidf_keyword_extractor.py` | TF-IDF fallback extractor |
| `app/routes/keywords.py` | API route: `POST /api/keywords/extract` |
| `app/schemas/keyword.py` | Pydantic request/response schemas |

### API Usage

```http
POST /api/keywords/extract
Content-Type: application/json

{
  "text": "Apple announced a new artificial intelligence chip...",
  "top_n": 10
}
```

```json
{
  "keywords": [
    {"keyword": "artificial intelligence chip", "score": 0.014},
    {"keyword": "Apple announced", "score": 0.021}
  ],
  "method": "yake",
  "total": 2,
  "note": "YAKE score: lower value = higher relevance. This is a statistical relevance score, NOT a probability or confidence."
}
```

### Benchmark (Manual Sample)

On a 200-word article about Apple AI chip:

| Algorithm | Time    | Quality |
|-----------|---------|---------|
| YAKE      | ~24ms   | Multi-word keyphrases, context-aware |
| TF-IDF    | ~16ms   | Good single-word terms, less context |

> Note: No ground-truth annotation available for accuracy comparison. These are qualitative observations on a manual sample.
