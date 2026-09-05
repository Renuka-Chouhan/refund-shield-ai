"""
RefundShield AI - Feature Engineering Pipeline
Computes 25+ domain features across customer history, identity signals, order value,
return discrepancy, carrier risk, merchant leakage, and payment chargebacks.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional, Any

FEATURE_COLUMNS = [
    "order_amount",
    "customer_order_count",
    "customer_return_count",
    "return_rate",
    "refund_count",
    "refund_amount",
    "address_changes",
    "phone_changes",
    "account_count",
    "device_account_count",
    "original_weight_kg",
    "returned_weight_kg",
    "weight_difference_pct",
    "previous_fraud",
    "chargeback_count",
    "merchant_return_rate",
    "delivery_partner_risk",
    "item_match_flag",
    "is_fashion",
    "is_electronics",
    "is_high_value",
    "condition_used",
    "condition_missing",
    "package_tampered",
    "days_to_return"
]


def extract_features_from_training_data(df_training: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Extracts numerical and encoded feature matrix X, binary label y_fraud, 
    and multi-class label y_type from fraud_training_data.csv.
    """
    df = df_training.copy()

    # Derived categorical indicators
    df["is_fashion"] = 0
    df["is_electronics"] = 0
    df["is_high_value"] = (df["order_amount"] >= 15000).astype(int)

    # Product condition flags
    df["condition_used"] = (df["product_condition"].str.lower() == "used").astype(int)
    df["condition_missing"] = (df["product_condition"].str.lower() == "missing").astype(int)
    
    # Defaults for optional columns if not present
    if "package_tampered" not in df.columns:
        df["package_tampered"] = 0
    if "days_to_return" not in df.columns:
        df["days_to_return"] = 3.0

    # Ensure all required feature columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    X = df[FEATURE_COLUMNS].copy()
    
    # Fill any null values with safe medians/zeros
    X = X.fillna({
        "customer_order_count": 1.0,
        "customer_return_count": 0.0,
        "return_rate": 0.0,
        "refund_count": 0.0,
        "refund_amount": 0.0,
        "address_changes": 0,
        "phone_changes": 0,
        "account_count": 1,
        "device_account_count": 1,
        "original_weight_kg": 1.0,
        "returned_weight_kg": 1.0,
        "weight_difference_pct": 0.0,
        "previous_fraud": 0,
        "chargeback_count": 0,
        "merchant_return_rate": 15.0,
        "delivery_partner_risk": 20.0,
        "item_match_flag": 1.0,
        "package_tampered": 0,
        "days_to_return": 3.0
    })

    y_fraud = df["fraud_label"].astype(int)
    y_type = df["fraud_type"].astype(str)

    return X, y_fraud, y_type


def build_inference_feature_vector(order_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Converts a single transaction dictionary (e.g. from user input or live API)
    into a standardized single-row DataFrame matching FEATURE_COLUMNS.
    """
    amt = float(order_dict.get("order_amount", 1500.0))
    cat = str(order_dict.get("category", "General")).lower()
    c_orders = float(order_dict.get("customer_order_count", 1))
    c_returns = float(order_dict.get("customer_return_count", 0))
    ret_rate = float(order_dict.get("return_rate", (c_returns / max(1, c_orders)) * 100.0))
    orig_wt = float(order_dict.get("original_weight_kg", 1.5))
    ret_wt = float(order_dict.get("returned_weight_kg", 1.5))

    if orig_wt > 0 and ret_wt >= 0:
        wt_diff_pct = round(((orig_wt - ret_wt) / orig_wt) * 100.0, 2)
    else:
        wt_diff_pct = float(order_dict.get("weight_difference_pct", 0.0))

    cond = str(order_dict.get("product_condition", "Good")).lower()

    row = {
        "order_amount": amt,
        "customer_order_count": c_orders,
        "customer_return_count": c_returns,
        "return_rate": ret_rate,
        "refund_count": float(order_dict.get("refund_count", c_returns)),
        "refund_amount": float(order_dict.get("refund_amount", c_returns * amt)),
        "address_changes": int(order_dict.get("address_changes", 0)),
        "phone_changes": int(order_dict.get("phone_changes", 0)),
        "account_count": int(order_dict.get("account_count", 1)),
        "device_account_count": int(order_dict.get("device_account_count", 1)),
        "original_weight_kg": orig_wt,
        "returned_weight_kg": ret_wt,
        "weight_difference_pct": wt_diff_pct,
        "previous_fraud": int(order_dict.get("previous_fraud", 0)),
        "chargeback_count": int(order_dict.get("chargeback_count", 0)),
        "merchant_return_rate": float(order_dict.get("merchant_return_rate", 15.0)),
        "delivery_partner_risk": float(order_dict.get("delivery_partner_risk", 25.0)),
        "item_match_flag": float(order_dict.get("item_match_flag", 1.0)),
        "is_fashion": 1 if "fashion" in cat or "cloth" in cat else 0,
        "is_electronics": 1 if "elec" in cat or "phone" in cat else 0,
        "is_high_value": 1 if amt >= 15000 else 0,
        "condition_used": 1 if "used" in cond else 0,
        "condition_missing": 1 if "missing" in cond or "empty" in cond else 0,
        "package_tampered": int(order_dict.get("package_tampered", 0)),
        "days_to_return": float(order_dict.get("days_to_return", 3.0))
    }

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


if __name__ == "__main__":
    from src.data.data_loader import load_raw_tables
    tables = load_raw_tables()
    df_train = tables.get("fraud_training_data", pd.DataFrame())
    if not df_train.empty:
        X, y_f, y_t = extract_features_from_training_data(df_train)
        print(f"[FeatureEngineering] Feature matrix shape: {X.shape}")
        print("[FeatureEngineering] Features:", list(X.columns))
        print("[FeatureEngineering] Fraud distribution:\n", y_f.value_counts())
        print("[FeatureEngineering] Sample inference vector:\n", build_inference_feature_vector({"order_amount": 12000, "category": "Fashion"}).iloc[0].to_dict())
