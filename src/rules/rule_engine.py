"""
RefundShield AI - Rule-Based Fraud Detection Engine
Configurable business rules that evaluate customer behavior, physical return metrics,
identity mutations, courier risk, and payment anomalies.
"""

from typing import Dict, Any, List, Tuple


class RuleEngine:
    """
    Evaluates business rules and computes a transparent, explainable rule score (0-100).
    """

    def __init__(self, thresholds: Dict[str, Any] = None):
        # Default configurable thresholds and weights
        self.thresholds = {
            "high_return_rate_threshold": 65.0,        # %
            "extreme_return_rate_threshold": 80.0,     # %
            "weight_loss_pct_threshold": 25.0,         # %
            "extreme_weight_loss_threshold": 50.0,     # %
            "multi_account_device_threshold": 2,       # accounts
            "address_change_threshold": 2,             # count
            "phone_change_threshold": 2,               # count
            "high_value_order_threshold": 15000.0,     # currency
            "courier_risk_threshold": 45,              # risk score
            "merchant_risk_threshold": 45,             # risk score
        }
        if thresholds:
            self.thresholds.update(thresholds)

    def evaluate(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a transaction dictionary against all business rules.
        Returns:
            {
                "rule_score": float (0-100),
                "triggered_rules": [
                    {"rule_id": str, "points": int, "description": str}
                ],
                "penalty_points": int,
                "credit_points": int
            }
        """
        triggered_rules = []
        penalty_points = 0
        credit_points = 0

        # Extract values with safe defaults
        ret_rate = float(transaction.get("return_rate", 0.0))
        cust_orders = int(transaction.get("customer_order_count", 1))
        order_amt = float(transaction.get("order_amount", 0.0))
        addr_changes = int(transaction.get("address_changes", 0))
        phone_changes = int(transaction.get("phone_changes", 0))
        dev_accounts = int(transaction.get("device_account_count", 1))
        item_match = float(transaction.get("item_match_flag", 1.0))
        orig_wt = float(transaction.get("original_weight_kg", 0.0))
        ret_wt = float(transaction.get("returned_weight_kg", 0.0))
        wt_diff_pct = float(transaction.get("weight_difference_pct", 0.0))
        prev_fraud = int(transaction.get("previous_fraud", 0))
        chargebacks = int(transaction.get("chargeback_count", 0))
        prod_cond = str(transaction.get("product_condition", "Good")).lower()
        category = str(transaction.get("category", "")).lower()
        dp_risk = float(transaction.get("delivery_partner_risk", 0.0))
        tampered = int(transaction.get("package_tampered", 0))
        m_rate = float(transaction.get("merchant_return_rate", 0.0))
        ret_reason = str(transaction.get("return_reason", "")).lower()
        acct_age = int(transaction.get("account_age_days", 100))

        # Recompute weight loss pct if weights are provided
        if orig_wt > 0 and ret_wt > 0:
            calculated_diff = ((orig_wt - ret_wt) / orig_wt) * 100.0
            wt_diff_pct = max(wt_diff_pct, calculated_diff)

        # 1. Extreme / High Return Rate Rule
        if cust_orders >= 2:
            if ret_rate >= self.thresholds["extreme_return_rate_threshold"]:
                pts = 25
                penalty_points += pts
                triggered_rules.append({
                    "rule_id": "RULE_EXTREME_RETURN_RATE",
                    "points": pts,
                    "description": f"+{pts}: Extremely high return rate ({ret_rate:.1f}%) across {cust_orders} orders"
                })
            elif ret_rate >= self.thresholds["high_return_rate_threshold"]:
                pts = 15
                penalty_points += pts
                triggered_rules.append({
                    "rule_id": "RULE_HIGH_RETURN_RATE",
                    "points": pts,
                    "description": f"+{pts}: Elevated return-to-order ratio ({ret_rate:.1f}%)"
                })

        # 2. Package Weight Discrepancy / Empty Box Rule
        if wt_diff_pct >= self.thresholds["extreme_weight_loss_threshold"]:
            pts = 30
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_EMPTY_BOX_WEIGHT_LOSS",
                "points": pts,
                "description": f"+{pts}: Critical return package weight deficit ({wt_diff_pct:.1f}% loss) indicating empty box"
            })
        elif wt_diff_pct >= self.thresholds["weight_loss_pct_threshold"]:
            pts = 18
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_SUSPICIOUS_WEIGHT_LOSS",
                "points": pts,
                "description": f"+{pts}: Significant package weight discrepancy ({wt_diff_pct:.1f}% loss)"
            })

        # 3. Physical Item Mismatch Rule (Item Switching)
        if item_match == 0.0:
            pts = 25
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_ITEM_MISMATCH",
                "points": pts,
                "description": f"+{pts}: Inspection flagged returned item barcode/SKU does not match manifest"
            })

        # 4. Sybil Device Sharing Rule
        if dev_accounts > self.thresholds["multi_account_device_threshold"]:
            pts = 20
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_DEVICE_SYBIL_RING",
                "points": pts,
                "description": f"+{pts}: Device hardware fingerprint linked to {dev_accounts} active accounts"
            })

        # 5. Address Mutation Velocity Rule
        if addr_changes >= self.thresholds["address_change_threshold"]:
            pts = 15
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_RAPID_ADDRESS_CHANGES",
                "points": pts,
                "description": f"+{pts}: Customer registered {addr_changes} distinct delivery addresses"
            })

        # 6. Phone Mutation Velocity Rule
        if phone_changes >= self.thresholds["phone_change_threshold"]:
            pts = 15
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_RAPID_PHONE_CHANGES",
                "points": pts,
                "description": f"+{pts}: Customer cycled through {phone_changes} distinct phone numbers"
            })

        # 7. Previous Confirmed Fraud Abuse
        if prev_fraud == 1:
            pts = 20
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_PRIOR_FRAUD_HISTORY",
                "points": pts,
                "description": f"+{pts}: Customer profile has confirmed prior fraud/abuse flags"
            })

        # 8. Payment Chargeback Abuse
        if chargebacks > 0:
            pts = 20
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_CHARGEBACK_DISPUTE",
                "points": pts,
                "description": f"+{pts}: Prior bank payment dispute/chargeback filed on this account"
            })

        # 9. Wardrobing Indicator: Used condition or tag removal on Fashion
        if ("fashion" in category or "cloth" in category or "apparel" in category) and prod_cond == "used":
            pts = 20
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_WARDROBING_USED_FASHION",
                "points": pts,
                "description": f"+{pts}: Fashion item returned in 'Used' condition (Wardrobing indicator)"
            })

        # 10. High-Value Return Exposure
        if order_amt >= self.thresholds["high_value_order_threshold"]:
            pts = 10
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_HIGH_VALUE_EXPOSURE",
                "points": pts,
                "description": f"+{pts}: High-value order (Rs. {order_amt:,.2f}) amplifies return financial risk"
            })

        # 11. Delivery Tampering / Courier Risk
        if tampered == 1 or dp_risk >= self.thresholds["courier_risk_threshold"]:
            pts = 15
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_DELIVERY_TAMPERING_RISK",
                "points": pts,
                "description": f"+{pts}: Route handled by courier with high tampering index (Risk score: {dp_risk})"
            })

        # 12. Fake Item Not Received Claim
        if "not received" in ret_reason:
            pts = 15
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_FAKE_INR_CLAIM",
                "points": pts,
                "description": f"+{pts}: Customer filed 'Item Not Received' dispute on tracked delivery"
            })

        # 13. Merchant Return Anomaly
        if m_rate >= self.thresholds["merchant_risk_threshold"]:
            pts = 10
            penalty_points += pts
            triggered_rules.append({
                "rule_id": "RULE_MERCHANT_ANOMALY",
                "points": pts,
                "description": f"+{pts}: Origin merchant shows elevated return leakage ({m_rate:.1f}%)"
            })

        # 14. Trust Credit for Established Shoppers (Loyalty Bonus)
        if prev_fraud == 0 and acct_age >= 180 and ret_rate < 25.0 and cust_orders >= 3:
            pts = 15
            credit_points += pts
            triggered_rules.append({
                "rule_id": "RULE_LOYAL_CUSTOMER_CREDIT",
                "points": -pts,
                "description": f"-{pts}: Trust bonus for established customer ({acct_age} days old, low return rate)"
            })

        # Calculate final net score clamped to [0, 100]
        raw_score = penalty_points - credit_points
        final_rule_score = min(100.0, max(0.0, float(raw_score)))

        return {
            "rule_score": round(final_rule_score, 1),
            "triggered_rules": triggered_rules,
            "penalty_points": penalty_points,
            "credit_points": credit_points
        }


if __name__ == "__main__":
    engine = RuleEngine()
    test_sample = {
        "order_amount": 28000,
        "customer_order_count": 6,
        "return_rate": 83.3,
        "device_account_count": 4,
        "address_changes": 3,
        "original_weight_kg": 2.5,
        "returned_weight_kg": 0.3,
        "item_match_flag": 0.0,
        "previous_fraud": 1,
        "product_condition": "Good"
    }
    result = engine.evaluate(test_sample)
    print("[RuleEngine] Evaluation Result for high-risk test sample:")
    print(f"  Score: {result['rule_score']}/100")
    print("  Triggered Rules:")
    for r in result["triggered_rules"]:
        print(f"    - {r['description']}")
