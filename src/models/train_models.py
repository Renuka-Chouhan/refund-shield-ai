"""
RefundShield AI - Model Training Pipeline
Trains Random Forest and XGBoost classifiers on feature-engineered fraud data.
Applies cross-validation, handles class imbalance, extracts feature importances,
and persists production models with joblib.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score
)
from xgboost import XGBClassifier

from src.data.data_loader import load_raw_tables
from src.data.feature_engineering import extract_features_from_training_data, FEATURE_COLUMNS

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_models() -> Dict[str, Any]:
    """
    Loads training data, extracts features, trains Random Forest & XGBoost,
    evaluates on test split, and saves model artifacts.
    """
    tables = load_raw_tables()
    df_train = tables.get("fraud_training_data")
    if df_train is None or df_train.empty:
        raise ValueError("fraud_training_data table is missing.")

    print(f"[ModelTraining] Loaded {len(df_train)} training instances.")
    X, y_fraud, y_type = extract_features_from_training_data(df_train)

    # Stratified Train-Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_fraud, test_size=0.20, random_state=42, stratify=y_fraud
    )
    print(f"[ModelTraining] Train shape: {X_train.shape}, Test shape: {X_test.shape}")

    # Compute scale_pos_weight for XGBoost to handle any imbalance
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos = float(neg_count) / max(1, float(pos_count))

    # 1. Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)

    # 2. XGBoost Classifier
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale_pos,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train, y_train)

    # Evaluate models on Test set
    models = {"Random Forest": rf, "XGBoost": xgb}
    metrics = {}

    for name, model in models.items():
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.50).astype(int)

        roc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)
        f1 = f1_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist()

        metrics[name] = {
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "f1_score": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "confusion_matrix": cm
        }

        print(f"\n[ModelTraining] --- {name} Evaluation ---")
        print(f"  ROC-AUC: {roc:.4f}")
        print(f"  PR-AUC:  {pr_auc:.4f}")
        print(f"  F1:      {f1:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f}")
        print("  Confusion Matrix [TN, FP / FN, TP]:", cm)

    # 5-Fold Stratified Cross-Validation for XGBoost
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(xgb, X, y_fraud, cv=cv, scoring="roc_auc", n_jobs=-1)
    print(f"\n[ModelTraining] 5-Fold Stratified CV ROC-AUC (XGBoost): {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Feature Importance Analysis
    importances = pd.Series(xgb.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=False)
    print("\n[ModelTraining] Top 8 Features (XGBoost):")
    for feat, imp in importances.head(8).items():
        print(f"  - {feat}: {imp:.4f}")

    # Persist Models
    rf_path = os.path.join(MODELS_DIR, "random_forest_model.joblib")
    xgb_path = os.path.join(MODELS_DIR, "xgboost_model.joblib")
    feat_path = os.path.join(MODELS_DIR, "feature_columns.joblib")
    meta_path = os.path.join(MODELS_DIR, "model_metrics.joblib")

    joblib.dump(rf, rf_path)
    joblib.dump(xgb, xgb_path)
    joblib.dump(FEATURE_COLUMNS, feat_path)
    joblib.dump({
        "metrics": metrics,
        "cv_roc_mean": float(cv_scores.mean()),
        "cv_roc_std": float(cv_scores.std()),
        "feature_importances": importances.to_dict()
    }, meta_path)

    print(f"\n[ModelTraining] Saved models to {MODELS_DIR}")
    return {
        "metrics": metrics,
        "feature_importances": importances,
        "test_data": (X_test, y_test)
    }


if __name__ == "__main__":
    train_models()
