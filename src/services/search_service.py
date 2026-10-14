"""
RefundShield AI - Global Search & Autocomplete Service
Enables instant lookup across Customer IDs, Order IDs, Hardware Devices, and Phone Hashes.
"""

import sqlite3
from typing import List
from src.db.database import get_connection
from src.schemas.models import SearchResult


def global_search(query: str, limit: int = 12) -> List[SearchResult]:
    """
    Executes multi-entity search across customers, orders, devices, and phone identifiers.
    """
    q = query.strip().upper()
    if not q:
        return []

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    results: List[SearchResult] = []

    try:
        # 1. Search Customers
        cust_rows = cur.execute("""
            SELECT 
                c.customer_id, c.city, c.previous_fraud_flag,
                count(o.order_id) as total_orders,
                count(r.return_id) as total_returns
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            LEFT JOIN returns r ON o.order_id = r.order_id
            WHERE c.customer_id LIKE ? OR c.city LIKE ?
            GROUP BY c.customer_id
            ORDER BY c.previous_fraud_flag DESC, total_returns DESC
            LIMIT ?
        """, (f"%{q}%", f"%{q}%", limit)).fetchall()

        for c in cust_rows:
            o_cnt = int(c["total_orders"]) if c["total_orders"] else 0
            r_cnt = int(c["total_returns"]) if c["total_returns"] else 0
            ret_rate = round((r_cnt / max(1, o_cnt)) * 100.0, 1)
            prev_fraud = int(c["previous_fraud_flag"])

            if prev_fraud == 1 or ret_rate >= 70:
                tier = "High Risk"
                color = "#EF4444"
            elif ret_rate >= 35:
                tier = "Medium Risk"
                color = "#F59E0B"
            else:
                tier = "Low Risk"
                color = "#10B981"

            results.append(SearchResult(
                id=c["customer_id"],
                type="customer",
                label=f"Customer {c['customer_id']} ({c['city']})",
                subtitle=f"{o_cnt} Orders • {r_cnt} Returns ({ret_rate}%) • Prior Fraud: {'YES' if prev_fraud else 'NO'}",
                badge=tier,
                risk_hint=color
            ))

        # 2. Search Orders
        if len(results) < limit:
            order_rows = cur.execute("""
                SELECT 
                    o.order_id, o.customer_id, o.order_amount, o.category, o.order_date,
                    r.return_id, r.return_reason
                FROM orders o
                LEFT JOIN returns r ON o.order_id = r.order_id
                WHERE o.order_id LIKE ? OR o.customer_id LIKE ?
                ORDER BY o.order_date DESC
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", limit - len(results))).fetchall()

            for o in order_rows:
                is_ret = o["return_id"] is not None
                results.append(SearchResult(
                    id=o["order_id"],
                    type="order",
                    label=f"Order {o['order_id']} • Rs. {float(o['order_amount']):,.0f}",
                    subtitle=f"{o['category']} • Cust: {o['customer_id']} • {o['order_date']}" + (f" • Returned ({o['return_reason']})" if is_ret else ""),
                    badge="Return Requested" if is_ret else "Delivered",
                    risk_hint="#F59E0B" if is_ret else "#10B981"
                ))

        # 3. Search Hardware Devices
        if len(results) < limit:
            dev_rows = cur.execute("""
                SELECT device_id, max(account_count) as accounts, group_concat(customer_id) as custs
                FROM devices
                WHERE device_id LIKE ?
                GROUP BY device_id
                LIMIT ?
            """, (f"%{q}%", limit - len(results))).fetchall()

            for d in dev_rows:
                acc_cnt = int(d["accounts"]) if d["accounts"] else 1
                results.append(SearchResult(
                    id=d["device_id"],
                    type="device",
                    label=f"Device {d['device_id']}",
                    subtitle=f"Shared across {acc_cnt} account(s): {d['custs'] or ''}",
                    badge="Multi-Account" if acc_cnt >= 2 else "Single User",
                    risk_hint="#EF4444" if acc_cnt >= 2 else "#10B981"
                ))

        return results
    finally:
        conn.close()
