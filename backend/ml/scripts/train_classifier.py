"""
Training Script -- News Category Classifier (Phase 4A)

Pipeline:
    AG News -> Preprocess -> TF-IDF -> 3 Models -> Evaluate -> Select Best -> Save

Models compared:
    1. TF-IDF + Multinomial Naive Bayes
    2. TF-IDF + Logistic Regression
    3. TF-IDF + Linear SVC (calibrated for probabilities)

Usage:
    python ml/scripts/train_classifier.py
"""

import io
import sys

# Force UTF-8 output on Windows (fixes cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

# Ensure backend/ is on sys.path
BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (no display required)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ml.scripts.preprocess import CATEGORIES, LABEL_COLUMN, TEXT_COLUMN, load_and_clean

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ML_DIR = BACKEND_DIR / "ml"
MODELS_DIR = ML_DIR / "models"
EVAL_DIR = ML_DIR / "evaluation"
MODELS_DIR.mkdir(exist_ok=True)
EVAL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "news_category_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
REPORT_PATH = EVAL_DIR / "classification_report.txt"
CM_PATH = EVAL_DIR / "confusion_matrix.png"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

RANDOM_STATE = 42
VALIDATION_SIZE = 0.15  # 15% validation from train
TEST_SPLIT_USED = "AG News native test split"

# ---------------------------------------------------------------------------
# TF-IDF shared configuration
# ---------------------------------------------------------------------------

TFIDF_PARAMS = dict(
    ngram_range=(1, 2),     # unigrams + bigrams
    min_df=2,               # ignore very rare terms
    max_df=0.95,            # ignore near-universal terms
    sublinear_tf=True,      # log(tf) scaling — helps with long docs
    max_features=100_000,   # vocabulary cap
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",  # words >= 2 chars
)


# ---------------------------------------------------------------------------
# Build pipelines
# ---------------------------------------------------------------------------

def build_pipelines() -> dict[str, Pipeline]:
    return {
        "Naive Bayes": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", MultinomialNB(alpha=0.1)),
        ]),
        "Logistic Regression": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(
                C=5.0,
                max_iter=1000,
                solver="lbfgs",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ]),
        "Linear SVM": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(
                LinearSVC(C=1.0, max_iter=2000, random_state=RANDOM_STATE),
                cv=3,
                method="isotonic",
            )),
        ]),
    }


# ---------------------------------------------------------------------------
# Evaluate one model
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
# Confusion matrix
# ---------------------------------------------------------------------------

def plot_confusion_matrix(y_true, y_pred, model_name: str, path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=CATEGORIES)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CATEGORIES,
        yticklabels=CATEGORIES,
        ax=ax,
        linewidths=0.5,
        linecolor="gray",
    )
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    plt.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Confusion matrix saved → {path}")


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 65)
    print("  AI NEWS ANALYZER — PHASE 4A CLASSIFIER TRAINING")
    print("=" * 65)

    # ── 1. Load & preprocess ─────────────────────────────────────────
    print("\n[1/6] Loading and preprocessing dataset...")
    train_full, test_df = load_and_clean()

    X_test = test_df[TEXT_COLUMN]
    y_test = test_df[LABEL_COLUMN]

    print(f"\n  Total training samples (before val split): {len(train_full):,}")
    print(f"  Test samples (AG News native):             {len(test_df):,}")

    # ── 2. Train / Validation split ───────────────────────────────────
    print("\n[2/6] Splitting train -> train + validation...")
    X_train, X_val, y_train, y_val = train_test_split(
        train_full[TEXT_COLUMN],
        train_full[LABEL_COLUMN],
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=train_full[LABEL_COLUMN],
    )
    print(f"  Train:      {len(X_train):,} samples")
    print(f"  Validation: {len(X_val):,} samples")
    print(f"  Test:       {len(X_test):,} samples")
    print(f"  Random state: {RANDOM_STATE}")

    # ── 3. Train all models ────────────────────────────────────────────
    print("\n[3/6] Training models...")
    pipelines = build_pipelines()
    val_results = {}

    for name, pipeline in pipelines.items():
        print(f"\n  Training: {name}")
        pipeline.fit(X_train, y_train)
        result = evaluate(pipeline, X_val, y_val, "validation")
        val_results[name] = result

    # ── 4. Select best model on validation ────────────────────────────
    print("\n[4/6] Selecting best model...")
    # Primary: Macro F1 (handles class balance properly)
    best_name = max(val_results, key=lambda n: (
        val_results[n]["macro_f1"],
        val_results[n]["weighted_f1"],
        val_results[n]["accuracy"],
    ))
    print(f"\n  Validation leaderboard:")
    for name, r in sorted(val_results.items(), key=lambda x: x[1]["macro_f1"], reverse=True):
        marker = " ← BEST" if name == best_name else ""
        print(f"    {name:<25} Acc={r['accuracy']:.4f}  MacroF1={r['macro_f1']:.4f}{marker}")

    best_pipeline = pipelines[best_name]

    # ── 5. Final evaluation on test set ───────────────────────────────
    print(f"\n[5/6] Final evaluation on TEST set ({best_name})...")
    test_result = evaluate(best_pipeline, X_test, y_test, "TEST (final)")

    full_report = (
        f"AI News Analyzer — Phase 4A Classification Report\n"
        f"{'='*55}\n"
        f"Dataset:       AG News (fancyzhx/ag_news)\n"
        f"Best Model:    {best_name}\n"
        f"Test Accuracy: {test_result['accuracy']:.4f}\n"
        f"Macro F1:      {test_result['macro_f1']:.4f}\n"
        f"Weighted F1:   {test_result['weighted_f1']:.4f}\n"
        f"{'='*55}\n\n"
        f"Validation results for all models:\n"
    )
    for name, r in val_results.items():
        full_report += (
            f"  {name}: Acc={r['accuracy']:.4f} MacroF1={r['macro_f1']:.4f}\n"
        )
    full_report += f"\n{'='*55}\nClassification Report (Test Set):\n{'='*55}\n\n"
    full_report += test_result["report"]

    REPORT_PATH.write_text(full_report, encoding="utf-8")
    print(f"\n  Classification report saved → {REPORT_PATH}")
    print(f"\n{test_result['report']}")

    # Validation reports for all models
    for name, r in val_results.items():
        report_path = EVAL_DIR / f"classification_report_{name.lower().replace(' ', '_')}_val.txt"
        report_path.write_text(r["report"], encoding="utf-8")

    # ── 5b. Confusion matrix ───────────────────────────────────────────
    plot_confusion_matrix(
        y_test, test_result["y_pred"],
        best_name, CM_PATH,
    )

    # ── 6. Save model + metadata ───────────────────────────────────────
    print(f"\n[6/6] Saving model artifacts...")
    joblib.dump(best_pipeline, MODEL_PATH, compress=3)
    model_size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
    print(f"  Model saved → {MODEL_PATH}  ({model_size_mb:.1f} MB)")

    metadata = {
        "model_name": best_name,
        "dataset": "AG News",
        "dataset_url": "https://huggingface.co/datasets/fancyzhx/ag_news",
        "dataset_license": "Unknown / Public use for research and portfolio",
        "categories": CATEGORIES,
        "num_categories": len(CATEGORIES),
        "label_mapping": {"0": "World", "1": "Sports", "2": "Business", "3": "Technology"},
        "text_column": TEXT_COLUMN,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "accuracy": test_result["accuracy"],
        "macro_f1": test_result["macro_f1"],
        "weighted_f1": test_result["weighted_f1"],
        "val_results": {
            name: {
                "accuracy": r["accuracy"],
                "macro_f1": r["macro_f1"],
                "weighted_f1": r["weighted_f1"],
            }
            for name, r in val_results.items()
        },
        "tfidf_params": {k: str(v) for k, v in TFIDF_PARAMS.items()},
        "random_state": RANDOM_STATE,
        "validation_size": VALIDATION_SIZE,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "phase": "4A",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"  Metadata saved → {METADATA_PATH}")

    print(f"\n{'='*65}")
    print(f"  TRAINING COMPLETE")
    print(f"  Best Model:    {best_name}")
    print(f"  Test Accuracy: {test_result['accuracy']:.4f}")
    print(f"  Macro F1:      {test_result['macro_f1']:.4f}")
    print(f"  Weighted F1:   {test_result['weighted_f1']:.4f}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
