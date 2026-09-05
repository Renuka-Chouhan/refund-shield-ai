"""
RefundShield AI - Model Evaluation & Reporting
Computes validation metrics, generates ROC curves, Precision-Recall curves,
confusion matrices, and feature importance charts, saving them to reports/figures/.
"""

import os
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix, auc

from src.data.data_loader import load_raw_tables
from src.data.feature_engineering import extract_features_from_training_data, FEATURE_COLUMNS

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports", "figures")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_evaluation_artifacts():
    """
    Generates publication-quality charts for the project report and documentation.
    """
    tables = load_raw_tables()
    df_train = tables.get("fraud_training_data")
    X, y_fraud, _ = extract_features_from_training_data(df_train)

    rf = joblib.load(os.path.join(MODELS_DIR, "random_forest_model.joblib"))
    xgb = joblib.load(os.path.join(MODELS_DIR, "xgboost_model.joblib"))

    # Style configuration
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. ROC Curves
    plt.figure(figsize=(8, 6))
    for name, model in [("Random Forest", rf), ("XGBoost", xgb)]:
        y_prob = model.predict_proba(X)[:, 1]
        fpr, tpr, _ = roc_curve(y_fraud, y_prob)
        roc_score = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_score:.3f})", linewidth=2)

    plt.plot([0, 1], [0, 1], "k--", label="Random Chance (AUC = 0.500)", alpha=0.6)
    plt.xlabel("False Positive Rate", fontsize=12, fontweight="bold")
    plt.ylabel("True Positive Rate (Recall)", fontsize=12, fontweight="bold")
    plt.title("RefundShield AI - Model ROC Curves", fontsize=14, fontweight="bold", pad=12)
    plt.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    roc_fig_path = os.path.join(REPORTS_DIR, "roc_curve.png")
    plt.savefig(roc_fig_path, dpi=300)
    plt.close()
    print(f"[Evaluator] Saved ROC curve -> {roc_fig_path}")

    # 2. Precision-Recall Curves
    plt.figure(figsize=(8, 6))
    for name, model in [("Random Forest", rf), ("XGBoost", xgb)]:
        y_prob = model.predict_proba(X)[:, 1]
        precision, recall, _ = precision_recall_curve(y_fraud, y_prob)
        pr_score = auc(recall, precision)
        plt.plot(recall, precision, label=f"{name} (PR-AUC = {pr_score:.3f})", linewidth=2)

    plt.xlabel("Recall", fontsize=12, fontweight="bold")
    plt.ylabel("Precision", fontsize=12, fontweight="bold")
    plt.title("RefundShield AI - Precision-Recall Curves", fontsize=14, fontweight="bold", pad=12)
    plt.legend(loc="lower left", frameon=True)
    plt.tight_layout()
    pr_fig_path = os.path.join(REPORTS_DIR, "precision_recall_curve.png")
    plt.savefig(pr_fig_path, dpi=300)
    plt.close()
    print(f"[Evaluator] Saved PR curve -> {pr_fig_path}")

    # 3. XGBoost Feature Importance Bar Chart
    importances = pd.Series(xgb.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=True)
    plt.figure(figsize=(10, 8))
    importances.tail(12).plot(kind="barh", color="#1E88E5", edgecolor="black")
    plt.xlabel("Relative Importance Weight", fontsize=12, fontweight="bold")
    plt.ylabel("Feature", fontsize=12, fontweight="bold")
    plt.title("RefundShield AI - Top 12 Predictive Fraud Features (XGBoost)", fontsize=14, fontweight="bold", pad=12)
    plt.tight_layout()
    feat_fig_path = os.path.join(REPORTS_DIR, "feature_importance.png")
    plt.savefig(feat_fig_path, dpi=300)
    plt.close()
    print(f"[Evaluator] Saved feature importance -> {feat_fig_path}")

    # 4. Confusion Matrix Heatmap (XGBoost)
    y_pred = xgb.predict(X)
    cm = confusion_matrix(y_fraud, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Legitimate", "Fraud"],
                yticklabels=["Legitimate", "Fraud"])
    plt.xlabel("Predicted Label", fontsize=12, fontweight="bold")
    plt.ylabel("Actual Label", fontsize=12, fontweight="bold")
    plt.title("Confusion Matrix - XGBoost Classifier", fontsize=14, fontweight="bold", pad=12)
    plt.tight_layout()
    cm_fig_path = os.path.join(REPORTS_DIR, "confusion_matrix.png")
    plt.savefig(cm_fig_path, dpi=300)
    plt.close()
    print(f"[Evaluator] Saved confusion matrix -> {cm_fig_path}")


if __name__ == "__main__":
    generate_evaluation_artifacts()
