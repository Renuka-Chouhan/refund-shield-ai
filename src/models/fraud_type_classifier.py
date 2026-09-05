"""
RefundShield AI - Fraud Typology Classifier
Multi-class machine learning classifier that categorizes suspicious events 
into specific fraud patterns: Wardrobing, Item Switching, Empty Box,
Serial Returning, Bracketing Abuse, Chargeback Fraud, Fake INR, etc.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from src.data.data_loader import load_raw_tables
from src.data.feature_engineering import extract_features_from_training_data, FEATURE_COLUMNS

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_fraud_type_classifier() -> Tuple[RandomForestClassifier, LabelEncoder]:
    """
    Trains and persists a multi-class Random Forest classifier for fraud typologies.
    """
    tables = load_raw_tables()
    df_train = tables.get("fraud_training_data")
    if df_train is None or df_train.empty:
        raise ValueError("fraud_training_data is missing.")

    X, _, y_type = extract_features_from_training_data(df_train)

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y_type)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )

    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n[FraudTypeClassifier] Multi-Class Evaluation Report:")
    target_names = [str(cls) for cls in encoder.classes_]
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

    # Persist model and encoder
    clf_path = os.path.join(MODELS_DIR, "fraud_type_classifier.joblib")
    enc_path = os.path.join(MODELS_DIR, "fraud_type_encoder.joblib")
    joblib.dump(clf, clf_path)
    joblib.dump(encoder, enc_path)
    print(f"[FraudTypeClassifier] Persisted typology classifier to {clf_path}")

    return clf, encoder


class FraudTypologyPredictor:
    """
    Inference helper for predicting probable fraud typology with confidence scores.
    """
    def __init__(self):
        clf_path = os.path.join(MODELS_DIR, "fraud_type_classifier.joblib")
        enc_path = os.path.join(MODELS_DIR, "fraud_type_encoder.joblib")
        if os.path.exists(clf_path) and os.path.exists(enc_path):
            self.model = joblib.load(clf_path)
            self.encoder = joblib.load(enc_path)
        else:
            self.model, self.encoder = train_fraud_type_classifier()

    def predict(self, feature_df: pd.DataFrame) -> Tuple[str, float]:
        """
        Predicts most probable fraud type and confidence probability.
        """
        probs = self.model.predict_proba(feature_df)[0]
        top_idx = int(np.argmax(probs))
        top_type = self.encoder.inverse_transform([top_idx])[0]
        confidence = float(probs[top_idx])
        return top_type, round(confidence, 4)


if __name__ == "__main__":
    train_fraud_type_classifier()
