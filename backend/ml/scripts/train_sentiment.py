"""
Training Script -- Sentiment Analysis (Phase 4B-1)

Pipeline:
    Zeroshot Financial News -> Preprocess -> TF-IDF -> 3 Models -> Evaluate -> Select Best -> Save

Models compared:
    1. TF-IDF + Multinomial Naive Bayes
    2. TF-IDF + Logistic Regression
    3. TF-IDF + Linear SVC (calibrated for probabilities)

Usage:
    python ml/scripts/train_sentiment.py
"""

import io
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ml.scripts.sentiment_preprocess import CATEGORIES, LABEL_COLUMN, TEXT_COLUMN, load_and_clean

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ML_DIR = BACKEND_DIR / "ml"
MODELS_DIR = ML_DIR / "models"
EVAL_DIR = ML_DIR / "evaluation"
MODELS_DIR.mkdir(exist_ok=True)
EVAL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "sentiment_model.joblib"
METADATA_PATH = MODELS_DIR / "sentiment_model_metadata.json"
REPORT_PATH = EVAL_DIR / "sentiment_classification_report.txt"
CM_PATH = EVAL_DIR / "sentiment_confusion_matrix.png"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RANDOM_STATE = 42
VALIDATION_SIZE = 0.15  # 15% from train

TFIDF_PARAMS = dict(
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    max_features=50_000,
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",
)

# ---------------------------------------------------------------------------
# Build pipelines
# ---------------------------------------------------------------------------

def build_pipelines() -> dict[str, Pipeline]:
    return {
        "Multinomial Naive Bayes": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", MultinomialNB(alpha=0.1)),
        ]),
        "Logistic Regression": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(
                C=2.0,
                max_iter=1000,
                solver="lbfgs",
                class_weight="balanced",  # handle Neutral dominance
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ]),
        "Linear SVM": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(
                LinearSVC(C=1.0, class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE),
                cv=3,
                method="isotonic",
            )),
        ]),
    }

# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate(pipeline: Pipeline, X: pd.Series, y: pd.Series, split_name: str) -> dict:
    y_pred = pipeline.predict(X)
    acc = accuracy_score(y, y_pred)
    macro_f1 = f1_score(y, y_pred, average="macro")
    weighted_f1 = f1_score(y, y_pred, average="weighted")
    report = classification_report(y, y_pred, target_names=CATEGORIES)

    print(f"\n  [{split_name}] Accuracy={acc:.4f}  MacroF1={macro_f1:.4f}  WeightedF1={weighted_f1:.4f}")

    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "report": report,
        "y_pred": y_pred,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 65)
    print("  AI NEWS ANALYZER -- PHASE 4B-1 SENTIMENT TRAINING")
    print("=" * 65)

    print("\n[1/6] Loading dataset...")
    # The dataset has native train (9543) and validation (2388).
    # We will use native validation as our TEST set, and split train into Train/Val.
    train_raw, test_df = load_and_clean()

    X_test = test_df[TEXT_COLUMN]
    y_test = test_df[LABEL_COLUMN]

    print("\n[2/6] Splitting train -> train + validation...")
    X_train, X_val, y_train, y_val = train_test_split(
        train_raw[TEXT_COLUMN],
        train_raw[LABEL_COLUMN],
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=train_raw[LABEL_COLUMN],
    )
    print(f"  Train:      {len(X_train):,} samples")
    print(f"  Validation: {len(X_val):,} samples")
    print(f"  Test:       {len(X_test):,} samples (from native validation)")

    print("\n[3/6] Training models...")
    pipelines = build_pipelines()
    val_results = {}

    for name, pipeline in pipelines.items():
        print(f"\n  Training: {name}")
        pipeline.fit(X_train, y_train)
        result = evaluate(pipeline, X_val, y_val, "validation")
        val_results[name] = result

    print("\n[4/6] Selecting best model...")
    best_name = max(val_results, key=lambda n: val_results[n]["macro_f1"])
    print(f"\n  Validation leaderboard:")
    for name, r in sorted(val_results.items(), key=lambda x: x[1]["macro_f1"], reverse=True):
        marker = " <- BEST" if name == best_name else ""
        print(f"    {name:<25} Acc={r['accuracy']:.4f}  MacroF1={r['macro_f1']:.4f}{marker}")

    best_pipeline = pipelines[best_name]

    print(f"\n[5/6] Final evaluation on TEST set ({best_name})...")
    test_result = evaluate(best_pipeline, X_test, y_test, "TEST")

    full_report = (
        f"AI News Analyzer -- Sentiment Classification Report\n"
        f"{'='*55}\n"
        f"Dataset:       zeroshot/twitter-financial-news-sentiment\n"
        f"Best Model:    {best_name}\n"
        f"Test Accuracy: {test_result['accuracy']:.4f}\n"
        f"Macro F1:      {test_result['macro_f1']:.4f}\n"
        f"Weighted F1:   {test_result['weighted_f1']:.4f}\n"
        f"{'='*55}\n\n"
        f"Classification Report (Test Set):\n{'='*55}\n\n"
        f"{test_result['report']}"
    )

    REPORT_PATH.write_text(full_report, encoding="utf-8")
    
    # Plot CM
    cm = confusion_matrix(y_test, test_result["y_pred"], labels=CATEGORIES)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CATEGORIES, yticklabels=CATEGORIES, ax=ax)
    ax.set_title(f"Sentiment Confusion Matrix -- {best_name}", pad=14)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.tight_layout()
    fig.savefig(CM_PATH, dpi=150)
    plt.close(fig)

    print(f"\n[6/6] Saving model artifacts...")
    joblib.dump(best_pipeline, MODEL_PATH, compress=3)

    metadata = {
        "model_name": best_name,
        "dataset": "zeroshot/twitter-financial-news-sentiment",
        "dataset_source": "Hugging Face Hub",
        "categories": CATEGORIES,
        "accuracy": test_result["accuracy"],
        "macro_f1": test_result["macro_f1"],
        "weighted_f1": test_result["weighted_f1"],
        "training_date": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "phase": "4B-1",
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "random_state": RANDOM_STATE
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n{'='*65}")
    print(f"  TRAINING COMPLETE")
    print(f"  Best Model:    {best_name}")
    print(f"  Test Accuracy: {test_result['accuracy']:.4f}")
    print(f"  Macro F1:      {test_result['macro_f1']:.4f}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
