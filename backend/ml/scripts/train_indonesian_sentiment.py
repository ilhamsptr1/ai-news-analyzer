"""
Training Script -- Indonesian Sentiment Classification (Phase 4B-1-ID)

Dataset: intanm/indonesian-financial-sentiment-analysis
Domain : Indonesian Financial News

Pipeline:
  Dataset -> Preprocess -> TF-IDF -> 3 Models -> GridSearch -> Eval -> Save

Usage:
    python ml/scripts/train_indonesian_sentiment.py
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
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedShuffleSplit, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ml.scripts.indonesian_sentiment_preprocess import (
    CLASSES,
    DATASET_DOMAIN,
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_SOURCE,
    LABEL_COLUMN,
    LABEL_ORIGIN,
    TEXT_COLUMN,
    load_and_clean,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ML_DIR = BACKEND_DIR / "ml"
MODELS_DIR = ML_DIR / "models"
EVAL_DIR = ML_DIR / "evaluation"
MODELS_DIR.mkdir(exist_ok=True)
EVAL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "sentiment_id_model.joblib"
METADATA_PATH = MODELS_DIR / "sentiment_id_metadata.json"
REPORT_PATH = EVAL_DIR / "indonesian_sentiment_classification_report.txt"
CM_PATH = EVAL_DIR / "indonesian_sentiment_confusion_matrix.png"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RANDOM_STATE = 42
VAL_SIZE = 0.15

TFIDF_PARAMS = dict(
    ngram_range=(1, 3),   # unigrams, bigrams, trigrams for sentiment (e.g. "tidak terlalu bagus")
    min_df=2,
    max_df=0.90,
    sublinear_tf=True,
    max_features=25_000,
    strip_accents="unicode",
    analyzer="word",
    lowercase=True,
    token_pattern=r"(?u)\b\w\w+\b",
)

# ---------------------------------------------------------------------------
# Build initial pipelines
# ---------------------------------------------------------------------------

def build_pipelines() -> dict[str, Pipeline]:
    return {
        "Multinomial Naive Bayes": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", MultinomialNB(alpha=0.5)),
        ]),
        "Logistic Regression": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(
                C=2.0,
                max_iter=1000,
                solver="lbfgs",
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ]),
        "Linear SVM": Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(
                LinearSVC(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=RANDOM_STATE,
                ),
                cv=3,
                method="isotonic",
            )),
        ]),
    }

# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate(pipeline: Pipeline, X, y, split_name: str) -> dict:
    y_pred = pipeline.predict(X)
    acc = accuracy_score(y, y_pred)
    macro_f1 = f1_score(y, y_pred, average="macro")
    weighted_f1 = f1_score(y, y_pred, average="weighted")
    report = classification_report(y, y_pred, target_names=CLASSES)
    print(f"  [{split_name}] Acc={acc:.4f}  MacroF1={macro_f1:.4f}  WeightedF1={weighted_f1:.4f}")
    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "report": report,
        "y_pred": y_pred,
    }

# ---------------------------------------------------------------------------
# GridSearch on winner
# ---------------------------------------------------------------------------

def tune_best(name: str, X_train, y_train) -> Pipeline:
    """Light GridSearch on the best-performing model type."""
    print(f"\n  Tuning: {name}")
    
    if "Naive Bayes" in name:
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", MultinomialNB()),
        ])
        param_grid = {"clf__alpha": [0.1, 0.5, 1.0, 2.0]}

    elif "Logistic" in name:
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(
                solver="lbfgs", class_weight="balanced",
                max_iter=1000, random_state=RANDOM_STATE, n_jobs=-1,
            )),
        ])
        param_grid = {"clf__C": [0.5, 1.0, 2.0, 5.0]}

    else:  # Linear SVM
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", CalibratedClassifierCV(
                LinearSVC(class_weight="balanced", max_iter=3000, random_state=RANDOM_STATE),
                cv=3, method="isotonic",
            )),
        ])
        param_grid = {"clf__estimator__C": [0.2, 0.5, 1.0, 2.0]}

    cv = StratifiedShuffleSplit(n_splits=3, test_size=0.15, random_state=RANDOM_STATE)
    gs = GridSearchCV(pipe, param_grid, cv=cv, scoring="f1_macro", n_jobs=-1, verbose=0)
    gs.fit(X_train, y_train)
    print(f"  Best params: {gs.best_params_}  CV MacroF1: {gs.best_score_:.4f}")
    return gs.best_estimator_

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 65)
    print("  AI NEWS ANALYZER -- PHASE 4B-1-ID INDONESIAN SENTIMENT")
    print("=" * 65)
    print(f"\n  *** Dataset : {DATASET_ID}")
    print(f"  *** Domain  : {DATASET_DOMAIN}")
    print(f"  *** Labels  : {LABEL_ORIGIN}\n")

    print("[1/7] Loading & preprocessing dataset...")
    train_raw, test_df = load_and_clean()
    X_test = test_df[TEXT_COLUMN]
    y_test = test_df[LABEL_COLUMN]

    # --- Data split ---
    print("\n[2/7] Splitting train -> train + validation (85/15 stratified)...")
    X_train, X_val, y_train, y_val = train_test_split(
        train_raw[TEXT_COLUMN],
        train_raw[LABEL_COLUMN],
        test_size=VAL_SIZE,
        random_state=RANDOM_STATE,
        stratify=train_raw[LABEL_COLUMN],
    )

    print(f"  Train:      {len(X_train):,} samples")
    print(f"  Validation: {len(X_val):,} samples")
    print(f"  Test:       {len(X_test):,} samples (native dataset test split)")
    print(f"\n  Class distribution (train):")
    print(y_train.value_counts().to_string())

    # --- Train all models ---
    print("\n[3/7] Training baseline models...")
    pipelines = build_pipelines()
    val_results = {}

    for name, pipeline in pipelines.items():
        print(f"\n  Training: {name}")
        pipeline.fit(X_train, y_train)
        result = evaluate(pipeline, X_val, y_val, "validation")
        val_results[name] = result

    # --- Select best ---
    print("\n[4/7] Selecting best model by Macro F1...")
    best_name = max(val_results, key=lambda n: val_results[n]["macro_f1"])
    print(f"\n  Validation leaderboard:")
    for name, r in sorted(val_results.items(), key=lambda x: x[1]["macro_f1"], reverse=True):
        marker = " <- BEST" if name == best_name else ""
        print(f"    {name:<28} Acc={r['accuracy']:.4f}  MacroF1={r['macro_f1']:.4f}{marker}")

    # --- GridSearch on best ---
    print("\n[5/7] Hyperparameter tuning on best model type...")
    tuned_pipeline = tune_best(best_name, X_train, y_train)
    tuned_val = evaluate(tuned_pipeline, X_val, y_val, "tuned-validation")

    # Use tuned if better
    if tuned_val["macro_f1"] >= val_results[best_name]["macro_f1"]:
        best_pipeline = tuned_pipeline
        print("  Using tuned model (equal or better on validation).")
    else:
        best_pipeline = pipelines[best_name]
        print("  Keeping original (tuned model was not better on validation).")

    # --- Final test evaluation ---
    print(f"\n[6/7] Final evaluation on TEST set ({best_name})...")
    test_result = evaluate(best_pipeline, X_test, y_test, "TEST")

    full_report = (
        f"AI News Analyzer -- Indonesian Sentiment Classification Report\n"
        f"{'='*60}\n"
        f"Dataset       : {DATASET_ID}\n"
        f"Domain        : {DATASET_DOMAIN}\n"
        f"Label Origin  : {LABEL_ORIGIN}\n"
        f"License       : {DATASET_LICENSE}\n"
        f"Best Model    : {best_name}\n"
        f"Test Accuracy : {test_result['accuracy']:.4f}\n"
        f"Macro F1      : {test_result['macro_f1']:.4f}\n"
        f"Weighted F1   : {test_result['weighted_f1']:.4f}\n"
        f"{'='*60}\n\n"
        f"Classification Report (Test Set):\n{'='*60}\n\n"
        f"{test_result['report']}"
    )
    REPORT_PATH.write_text(full_report, encoding="utf-8")

    # Confusion matrix
    cm = confusion_matrix(y_test, test_result["y_pred"], labels=CLASSES)
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=CLASSES, yticklabels=CLASSES, ax=ax
    )
    ax.set_title(f"Indonesian Sentiment -- Confusion Matrix ({best_name})", pad=14)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(CM_PATH, dpi=150)
    plt.close(fig)

    # --- Save ---
    print("\n[7/7] Saving model artifacts...")
    joblib.dump(best_pipeline, MODEL_PATH, compress=3)

    metadata = {
        "language": "id",
        "model_name": best_name,
        "dataset": DATASET_ID,
        "dataset_source": DATASET_SOURCE,
        "dataset_license": DATASET_LICENSE,
        "dataset_domain": DATASET_DOMAIN,
        "label_origin": LABEL_ORIGIN,
        "classes": CLASSES,
        "accuracy": test_result["accuracy"],
        "macro_f1": test_result["macro_f1"],
        "weighted_f1": test_result["weighted_f1"],
        "training_date": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "phase": "4B-1-ID",
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "random_state": RANDOM_STATE,
        "tfidf_lowercase": True,
        "calibration": "CalibratedClassifierCV" if "SVM" in best_name else None,
        "text_strategy": "text only",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*65}")
    print(f"  TRAINING COMPLETE")
    print(f"  Best Model    : {best_name}")
    print(f"  Test Accuracy : {test_result['accuracy']:.4f}")
    print(f"  Macro F1      : {test_result['macro_f1']:.4f}")
    print(f"  Model size    : {MODEL_PATH.stat().st_size / 1024:.1f} KB")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
