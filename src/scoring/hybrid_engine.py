"""
RefundShield AI - Hybrid Risk Scoring & Explainability Engine
Combines Rule-Based Scoring, Supervised Machine Learning, and Identity Network Graph Analysis
into a single, calibrated 0-100 Fraud Risk Score with point-by-point explainability.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.rules.rule_engine import RuleEngine
from src.data.feature_engineering import build_inference_feature_vector, FEATURE_COLUMNS
from src.models.fraud_type_classifier import FraudTypologyPredictor
from src.graph.network_analyzer import IdentityNetworkAnalyzer
from src.db.database import log_fraud_evaluation

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")


class HybridFraudEngine:
    """
    Unified Multi-Layer Fraud Detection Engine:
    Rule Engine + ML Classifier + Network Graph -> Hybrid Score (0-100) + Explainability
    """

    def __init__(
        self,
        weight_rule: float = 0.40,
        weight_ml: float = 0.45,
        weight_network: float = 0.15,
        rule_thresholds: Optional[Dict[str, Any]] = None
    ):
        self.w_rule = weight_rule
        self.w_ml = weight_ml
        self.w_network = weight_network

        # Load Rule Engine
        self.rule_engine = RuleEngine(rule_thresholds)

        # Load ML Models
        xgb_path = os.path.join(MODELS_DIR, "xgboost_model.joblib")
        rf_path = os.path.join(MODELS_DIR, "random_forest_model.joblib")

        if os.path.exists(xgb_path):
            self.ml_model = joblib.load(xgb_path)
            self.model_type = "XGBoost"
        elif os.path.exists(rf_path):
            self.ml_model = joblib.load(rf_path)
            self.model_type = "Random Forest"
        else:
            self.ml_model = None
            self.model_type = "Rule-Only Fallback"

        # Load Typology Predictor
        try:
            self.typology_predictor = FraudTypologyPredictor()
        except Exception:
            self.typology_predictor = None

        # Network Analyzer
        self.network_analyzer = IdentityNetworkAnalyzer()

    def evaluate_transaction(
        self,
        transaction_dict: Dict[str, Any],
        persist_audit: bool = True
    ) -> Dict[str, Any]:
        """
        Executes complete multi-layer fraud evaluation on an input order/return record.
        """
        cid = str(transaction_dict.get("customer_id", "UNKNOWN"))
        oid = str(transaction_dict.get("order_id", f"ORD_{int(datetime.now().timestamp())}"))

        # 1. Rule Engine Evaluation
        rule_res = self.rule_engine.evaluate(transaction_dict)
        rule_score = float(rule_res["rule_score"])
        triggered_rules = rule_res["triggered_rules"]

        # 2. Network Graph Risk Evaluation
        net_res = self.network_analyzer.evaluate_customer_network_risk(cid)
        net_points = float(net_res["network_risk_points"])

        # 3. Machine Learning Inference
        feature_df = build_inference_feature_vector(transaction_dict)
        if self.ml_model is not None:
            ml_prob = float(self.ml_model.predict_proba(feature_df)[0][1])
        else:
            ml_prob = rule_score / 100.0

        # 4. Probable Fraud Typology
        if self.typology_predictor is not None and (ml_prob >= 0.40 or rule_score >= 40):
            pred_type, type_conf = self.typology_predictor.predict(feature_df)
        else:
            pred_type = "Legitimate"
            type_conf = 0.95

        # 5. Hybrid Risk Score (0-100)
        ml_score = ml_prob * 100.0
        hybrid_raw = (self.w_rule * rule_score) + (self.w_ml * ml_score) + (self.w_network * (net_points * 3.33))
        
        # Override to high if critical fraud indicators are active (e.g. empty box or item mismatch)
        if transaction_dict.get("item_match_flag", 1.0) == 0.0 or transaction_dict.get("product_condition") == "Missing":
            hybrid_raw = max(hybrid_raw, 78.0)

        final_score = int(min(100, max(0, round(hybrid_raw))))

        # 6. Risk Level & Recommended Action
        if final_score >= 71:
            risk_level = "High Risk"
            action = "Investigate / Block"
            badge_color = "#E53935"
        elif final_score >= 31:
            risk_level = "Medium Risk"
            action = "Manual Review"
            badge_color = "#FB8C00"
        else:
            risk_level = "Low Risk"
            action = "Approve"
            badge_color = "#43A047"

        # 7. Itemized Reasons (Explainability)
        reasons = []
        for r in triggered_rules:
            reasons.append(r["description"])

        # Add ML and Network explanations
        if ml_prob >= 0.75:
            reasons.append(f"+20: ML Model ({self.model_type}) detected severe behavioral fraud signature (p={ml_prob:.2f})")
        elif ml_prob >= 0.50:
            reasons.append(f"+10: ML Model detected elevated refund risk probability (p={ml_prob:.2f})")

        if net_points > 0:
            reasons.append(f"+{int(net_points)}: Network Analysis: {net_res['description']}")

        if not reasons:
            reasons.append("Clean transaction: verified delivery, matched return, normal shopping cadence.")

        result = {
            "order_id": oid,
            "customer_id": cid,
            "hybrid_risk_score": final_score,
            "risk_level": risk_level,
            "recommended_action": action,
            "badge_color": badge_color,
            "probable_fraud_type": pred_type,
            "typology_confidence": type_conf,
            "rule_score": rule_score,
            "ml_probability": round(ml_prob, 4),
            "network_risk_points": net_points,
            "ring_size": net_res.get("ring_size", 1),
            "reasons": reasons,
            "triggered_rules": triggered_rules
        }

        # 8. Persist to SQLite Audit Log
        if persist_audit:
            try:
                eval_id = f"EV_{oid}_{int(datetime.now().timestamp())}"
                log_fraud_evaluation(
                    eval_id=eval_id,
                    order_id=oid,
                    customer_id=cid,
                    rule_score=rule_score,
                    ml_prob=ml_prob,
                    hybrid_score=final_score,
                    risk_level=risk_level,
                    action=action,
                    fraud_type=pred_type,
                    rules_json=str([r["rule_id"] for r in triggered_rules])
                )
            except Exception as e:
                pass

        return result


if __name__ == "__main__":
    engine = HybridFraudEngine()
    print("[HybridEngine] Testing sample suspicious order...")
    test_sample = {
        "order_id": "O99999",
        "customer_id": "C0005",
        "order_amount": 24500,
        "category": "Electronics",
        "customer_order_count": 8,
        "customer_return_count": 7,
        "return_rate": 87.5,
        "device_account_count": 3,
        "address_changes": 2,
        "phone_changes": 1,
        "original_weight_kg": 3.2,
        "returned_weight_kg": 0.4,
        "item_match_flag": 0.0,
        "product_condition": "Good",
        "previous_fraud": 1
    }
    evaluation = engine.evaluate_transaction(test_sample, persist_audit=False)
    print(f"Risk Score: {evaluation['hybrid_risk_score']}/100 -> {evaluation['risk_level']}")
    print(f"Action: {evaluation['recommended_action']}")
    print(f"Probable Type: {evaluation['probable_fraud_type']} (Conf: {evaluation['typology_confidence']:.2f})")
    print("Itemized Reasons:")
    for reason in evaluation["reasons"]:
        print(f"  - {reason}")
