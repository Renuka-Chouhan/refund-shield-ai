"""
RefundShield AI - Analytical Aggregation & Supply Chain Service
Computes real-time executive KPIs, fraud typology distributions, carrier tampering rates,
and syndicate ring topologies.
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, List

from src.db.database import get_connection
from src.schemas.models import KPIResponse
from src.graph.network_analyzer import IdentityNetworkAnalyzer
from src.data.data_loader import load_raw_tables


def get_executive_kpis(network_analyzer: IdentityNetworkAnalyzer) -> KPIResponse:
    """
    Computes system-wide executive metrics from SQLite database.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        total_orders = cur.execute("SELECT count(*) FROM orders").fetchone()[0] or 0
        total_spend = cur.execute("SELECT sum(order_amount) FROM orders").fetchone()[0] or 0.0
        total_returns = cur.execute("SELECT count(*) FROM returns").fetchone()[0] or 0
        total_refunds = cur.execute("SELECT sum(refund_amount) FROM refunds").fetchone()[0] or 0.0
        total_customers = cur.execute("SELECT count(*) FROM customers").fetchone()[0] or 0

        # Estimated fraud loss prevented & high risk accounts
        # Accounts with previous fraud or return rate >= 70%
        high_risk_stats = cur.execute("""
            SELECT count(DISTINCT c.customer_id) as hr_count, sum(o.order_amount) as hr_loss
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE c.previous_fraud_flag = 1
        """).fetchone()

        hr_count = int(high_risk_stats[0]) if high_risk_stats and high_risk_stats[0] else 0
        hr_loss = float(high_risk_stats[1]) if high_risk_stats and high_risk_stats[1] else 0.0

        rings = network_analyzer.find_fraud_rings(min_accounts=2)

        return_rate = round((total_returns / max(1, total_orders)) * 100.0, 1)
        refund_leakage = round((total_refunds / max(1.0, total_spend)) * 100.0, 1)
        hr_rate = round((hr_count / max(1, total_customers)) * 100.0, 1)

        return KPIResponse(
            total_orders=total_orders,
            total_spend=round(total_spend, 2),
            total_returns=total_returns,
            return_rate=return_rate,
            total_refunds=round(total_refunds, 2),
            refund_leakage_pct=refund_leakage,
            fraud_loss_intercepted=round(hr_loss, 2),
            high_risk_count=hr_count,
            high_risk_rate=hr_rate,
            total_customers=total_customers,
            sybil_rings_count=len(rings)
        )
    finally:
        conn.close()


def get_risk_distribution() -> List[Dict[str, Any]]:
    """
    Computes risk tier distribution across customer base.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        rows = cur.execute("""
            SELECT 
                c.customer_id, c.previous_fraud_flag,
                count(o.order_id) as total_orders,
                count(r.return_id) as total_returns
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            LEFT JOIN returns r ON o.order_id = r.order_id
            GROUP BY c.customer_id
        """).fetchall()

        tiers = {"Low": 0, "Medium": 0, "High": 0}
        for r in rows:
            o_cnt = int(r["total_orders"]) if r["total_orders"] else 0
            r_cnt = int(r["total_returns"]) if r["total_returns"] else 0
            ret_rate = (r_cnt / max(1, o_cnt)) * 100.0
            prev_fraud = int(r["previous_fraud_flag"])

            if prev_fraud == 1 or ret_rate >= 70:
                tiers["High"] += 1
            elif ret_rate >= 35 or o_cnt >= 10:
                tiers["Medium"] += 1
            else:
                tiers["Low"] += 1

        total = sum(tiers.values()) or 1
        return [
            {"tier": "Low Risk", "count": tiers["Low"], "percentage": round((tiers["Low"] / total) * 100, 1), "color": "#10B981"},
            {"tier": "Medium Risk", "count": tiers["Medium"], "percentage": round((tiers["Medium"] / total) * 100, 1), "color": "#F59E0B"},
            {"tier": "High Risk", "count": tiers["High"], "percentage": round((tiers["High"] / total) * 100, 1), "color": "#EF4444"}
        ]
    finally:
        conn.close()


def get_fraud_typologies() -> List[Dict[str, Any]]:
    """
    Aggregates financial exposure and average risk scores per fraud typology.
    """
    tables = load_raw_tables()
    df_train = tables.get("fraud_training_data", pd.DataFrame())

    if df_train.empty or "fraud_type" not in df_train.columns:
        return []

    agg = df_train.groupby("fraud_type").agg({
        "order_id": "count",
        "order_amount": "sum",
        "risk_score": "mean"
    }).reset_index()

    agg.columns = ["typology", "count", "total_exposure", "avg_risk_score"]
    agg = agg.sort_values(by="total_exposure", ascending=False)

    results = []
    for _, row in agg.iterrows():
        results.append({
            "typology": str(row["typology"]),
            "count": int(row["count"]),
            "total_exposure": round(float(row["total_exposure"]), 2),
            "avg_risk_score": round(float(row["avg_risk_score"]), 1)
        })

    return results


def get_supply_chain_risks() -> Dict[str, Any]:
    """
    Returns courier partner tampering rates and merchant leakage metrics.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        courier_rows = cur.execute("""
            SELECT delivery_partner_id, total_deliveries, return_complaints,
                   tampering_cases, suspicious_returns, partner_risk_score
            FROM delivery_partners
            ORDER BY partner_risk_score DESC
        """).fetchall()

        couriers = [dict(r) for r in courier_rows]

        merchant_rows = cur.execute("""
            SELECT merchant_id, category, total_orders, return_rate,
                   refund_rate, fraud_rate, merchant_risk_score
            FROM merchants
            ORDER BY merchant_risk_score DESC
        """).fetchall()

        merchants = [dict(r) for r in merchant_rows]

        return {
            "couriers": couriers,
            "merchants": merchants
        }
    finally:
        conn.close()
