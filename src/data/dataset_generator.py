"""
RefundShield AI - Realistic Dataset Simulation & Scaling Generator
Generates realistic, statistically coherent e-commerce transactional data 
modeling all 12+ refund fraud patterns, multi-account identity rings,
delivery partner collusion, and merchant leakage.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed")

CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Indore", "Bhopal", "Nagpur"]
CATEGORIES = {
    "Fashion": (600, 7500, 0.6),      # min_price, max_price, weight_kg
    "Electronics": (4000, 65000, 2.8),
    "Beauty": (400, 4500, 0.4),
    "Footwear": (900, 9500, 1.2),
    "Home": (800, 12000, 3.5),
    "Grocery": (250, 2500, 2.0)
}
PAYMENT_METHODS = ["UPI", "Card", "Net Banking", "Wallet", "COD"]
RETURN_REASONS = [
    "Changed mind", "Size issue", "Defective product", "Wrong Item", 
    "Item not received", "Duplicate order", "Color mismatch", "Package arrived damaged"
]

FRAUD_TYPES = [
    "Legitimate",
    "Wardrobing",
    "Item Switching",
    "Empty Box",
    "Serial Returning",
    "Bracketing Abuse",
    "Stolen Merchandise",
    "Price Switching",
    "Receipt Fraud",
    "Chargeback Fraud",
    "Fake INR",
    "Identity/Account Abuse",
    "Delivery Fraud",
    "Merchant Fraud"
]


def generate_benchmark_dataset(n_orders: int = 2500, output_dir: str = OUTPUT_DIR) -> Dict[str, pd.DataFrame]:
    """
    Generates a full relational benchmark dataset and writes CSVs to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[Generator] Synthesizing benchmark dataset with {n_orders} orders...")

    # 1. Delivery Partners (10 partners)
    n_partners = 10
    dp_data = []
    for i in range(1, n_partners + 1):
        partner_id = f"DP{i:03d}"
        total_deliv = random.randint(5000, 25000)
        # DP006 and DP009 are higher risk couriers
        is_risky_partner = (i in [6, 9])
        tampering = random.randint(35, 75) if is_risky_partner else random.randint(3, 18)
        suspicious = random.randint(45, 90) if is_risky_partner else random.randint(8, 30)
        complaints = tampering * 3 + random.randint(20, 80)
        risk_score = random.randint(60, 85) if is_risky_partner else random.randint(12, 38)
        
        dp_data.append({
            "delivery_partner_id": partner_id,
            "total_deliveries": total_deliv,
            "return_complaints": complaints,
            "tampering_cases": tampering,
            "suspicious_returns": suspicious,
            "partner_risk_score": risk_score
        })
    df_delivery_partners = pd.DataFrame(dp_data)

    # 2. Merchants (12 merchants)
    n_merchants = 12
    merchant_data = []
    merchant_cats = list(CATEGORIES.keys())
    for i in range(1, n_merchants + 1):
        mid = f"M{i:03d}"
        mcat = merchant_cats[(i - 1) % len(merchant_cats)]
        tot_ord = random.randint(4000, 18000)
        # M006 and M011 are high risk merchants
        is_risky_m = (i in [6, 11])
        ret_rate = round(random.uniform(22.0, 32.0), 1) if is_risky_m else round(random.uniform(8.0, 18.0), 1)
        ref_rate = round(ret_rate * random.uniform(0.85, 1.05), 1)
        fraud_rate = round(random.uniform(3.5, 6.0), 1) if is_risky_m else round(random.uniform(0.8, 2.2), 1)
        m_risk = random.randint(55, 80) if is_risky_m else random.randint(15, 42)
        
        merchant_data.append({
            "merchant_id": mid,
            "category": mcat,
            "total_orders": tot_ord,
            "return_rate": ret_rate,
            "refund_rate": ref_rate,
            "fraud_rate": fraud_rate,
            "merchant_risk_score": m_risk
        })
    df_merchants = pd.DataFrame(merchant_data)

    # 3. Customers (450 customers)
    n_customers = 450
    customer_data = []
    # Designate fraud cohorts:
    # Sybil ring 1: C0020 - C0025 share device DEV001 and phone PH001
    # Sybil ring 2: C0080 - C0085 share device DEV002
    sybil_group_1 = [f"C{c:04d}" for c in range(20, 26)]
    sybil_group_2 = [f"C{c:04d}" for c in range(80, 86)]
    wardrobers = [f"C{c:04d}" for c in range(30, 42)]
    serial_returners = [f"C{c:04d}" for c in range(50, 65)]
    item_switchers = [f"C{c:04d}" for c in range(70, 78)]
    chargeback_abusers = [f"C{c:04d}" for c in range(90, 98)]

    for i in range(1, n_customers + 1):
        cid = f"C{i:04d}"
        age_days = random.randint(20, 950)
        reg_date = (datetime(2026, 9, 1) - timedelta(days=age_days)).strftime("%Y-%m-%d")
        gender = random.choice(["M", "F"])
        city = random.choice(CITIES)
        
        # Fraud flag
        is_known_fraud = 1 if (cid in sybil_group_1 or cid in item_switchers or cid in chargeback_abusers or random.random() < 0.05) else 0
        account_status = "Suspended" if (is_known_fraud and random.random() < 0.15) else "Active"
        
        customer_data.append({
            "customer_id": cid,
            "account_age_days": age_days,
            "registration_date": reg_date,
            "gender": gender,
            "city": city,
            "previous_fraud_flag": is_known_fraud,
            "account_status": account_status
        })
    df_customers = pd.DataFrame(customer_data)

    # 4. Identity Links and Devices
    # Devices: total 320 unique devices
    identity_records = []
    device_records = []
    
    # Pre-assign base devices and addresses
    customer_base_profile = {}
    for i in range(1, n_customers + 1):
        cid = f"C{i:04d}"
        if cid in sybil_group_1:
            dev = "DEV_RING_001"
            ph = "PH_RING_001"
            add = "ADD_RING_001"
            pf = "PF_RING_001"
        elif cid in sybil_group_2:
            dev = "DEV_RING_002"
            ph = f"PH_{random.randint(100, 110):04d}"
            add = "ADD_RING_002"
            pf = f"PF_{random.randint(200, 210):04d}"
        else:
            dev = f"DEV{random.randint(1, 350):04d}"
            ph = f"PH{random.randint(1, 400):04d}"
            add = f"ADD{random.randint(1, 400):04d}"
            pf = f"PF{random.randint(1, 400):04d}"
        
        customer_base_profile[cid] = {
            "device_id": dev,
            "phone_hash": ph,
            "address_id": add,
            "payment_fingerprint": pf
        }

    # 5. Orders, Payments, Deliveries, Returns, Refunds Generation
    order_data = []
    payment_data = []
    delivery_data = []
    return_data = []
    refund_data = []
    fraud_eval_data = []

    start_date = datetime(2026, 5, 1)
    end_date = datetime(2026, 9, 1)
    days_range = (end_date - start_date).days

    order_counter = 0
    return_counter = 0
    refund_counter = 0

    # Group customers with assigned frequency
    customer_order_history = {c: [] for c in df_customers["customer_id"]}

    for o_idx in range(1, n_orders + 1):
        order_counter += 1
        order_id = f"O{order_counter:05d}"
        
        # Pick customer (skewed towards frequent repeaters / abusers)
        r_val = random.random()
        if r_val < 0.15:
            cid = random.choice(serial_returners)
        elif r_val < 0.25:
            cid = random.choice(wardrobers)
        elif r_val < 0.35:
            cid = random.choice(sybil_group_1 + sybil_group_2)
        elif r_val < 0.42:
            cid = random.choice(item_switchers + chargeback_abusers)
        else:
            cid = random.choice(df_customers["customer_id"])
            
        c_prof = customer_base_profile[cid]
        c_row = df_customers[df_customers["customer_id"] == cid].iloc[0]

        # Pick merchant & category
        m_row = df_merchants.sample(1).iloc[0]
        mid = m_row["merchant_id"]
        
        # Biasing category based on fraud cohort
        if cid in wardrobers:
            category = "Fashion"
        elif cid in item_switchers:
            category = "Electronics"
        else:
            category = m_row["category"]

        min_p, max_p, base_wt = CATEGORIES[category]
        order_amount = round(random.uniform(min_p, max_p), 2)
        quantity = random.randint(3, 6) if (cid in serial_returners and random.random() < 0.4) else random.randint(1, 2)
        discount = round(order_amount * random.uniform(0.02, 0.18), 2)
        order_date = start_date + timedelta(days=random.randint(0, days_range - 10))
        order_date_str = order_date.strftime("%Y-%m-%d")
        pid = f"P{random.randint(1, 250):04d}"
        pay_id = f"PAY{order_counter:05d}"

        order_data.append({
            "order_id": order_id,
            "customer_id": cid,
            "merchant_id": mid,
            "product_id": pid,
            "category": category,
            "order_amount": order_amount,
            "order_date": order_date_str,
            "quantity": quantity,
            "discount_amount": discount,
            "payment_id": pay_id
        })
        customer_order_history[cid].append(order_id)

        # Identity record for this order
        # Address/phone mutation simulation
        addr = c_prof["address_id"]
        phone = c_prof["phone_hash"]
        dev = c_prof["device_id"]
        pf = c_prof["payment_fingerprint"]

        if cid in sybil_group_1 or cid in sybil_group_2 or random.random() < 0.08:
            # Frequent address mutation
            addr = f"ADD_{cid}_{random.randint(1, 4)}"
            if random.random() < 0.3:
                phone = f"PH_{cid}_{random.randint(1, 3)}"

        identity_records.append({
            "customer_id": cid,
            "address_id": addr,
            "phone_hash": phone,
            "device_id": dev,
            "payment_fingerprint": pf
        })

        # Payment
        pay_method = random.choice(PAYMENT_METHODS)
        # Chargeback abuser behavior
        is_chargeback = 1 if (cid in chargeback_abusers and random.random() < 0.65) else (1 if random.random() < 0.015 else 0)
        cb_amt = order_amount if is_chargeback else 0.0
        attempts = random.randint(2, 4) if (is_chargeback or random.random() < 0.05) else 1

        payment_data.append({
            "payment_id": pay_id,
            "order_id": order_id,
            "payment_method": pay_method,
            "payment_amount": order_amount,
            "payment_status": "Success",
            "chargeback_flag": is_chargeback,
            "chargeback_amount": cb_amt,
            "payment_attempts": attempts
        })

        # Delivery
        deliv_id = f"D{order_counter:05d}"
        dp_row = df_delivery_partners.sample(1).iloc[0]
        dp_id = dp_row["delivery_partner_id"]
        deliv_date = order_date + timedelta(days=random.randint(2, 5))
        orig_weight = round(base_wt * quantity + random.uniform(-0.1, 0.3), 2)
        orig_weight = max(0.2, orig_weight)
        
        # Tampering happens more with risky delivery partners
        is_tampered = 1 if (dp_id in ["DP006", "DP009"] and random.random() < 0.18) else (1 if random.random() < 0.01 else 0)

        delivery_data.append({
            "delivery_id": deliv_id,
            "order_id": order_id,
            "delivery_partner_id": dp_id,
            "delivery_date": deliv_date.strftime("%Y-%m-%d"),
            "delivery_status": "Delivered",
            "original_weight_kg": orig_weight,
            "package_tampered": is_tampered,
            "delivery_location_id": f"LOC{random.randint(1, 30):03d}"
        })

        # Determine if return is requested
        will_return = False
        fraud_type = "Legitimate"
        fraud_label = 0

        if cid in wardrobers and category == "Fashion" and random.random() < 0.85:
            will_return = True
            fraud_type = "Wardrobing"
            fraud_label = 1
        elif cid in item_switchers and category == "Electronics" and random.random() < 0.85:
            will_return = True
            fraud_type = "Item Switching"
            fraud_label = 1
        elif cid in serial_returners and random.random() < 0.78:
            will_return = True
            fraud_type = "Serial Returning"
            fraud_label = 1
        elif cid in sybil_group_1 and random.random() < 0.70:
            will_return = True
            fraud_type = "Identity/Account Abuse"
            fraud_label = 1
        elif is_chargeback:
            # Chargeback fraud (may or may not return)
            fraud_type = "Chargeback Fraud"
            fraud_label = 1
            will_return = (random.random() < 0.40)
        elif is_tampered:
            fraud_type = "Delivery Fraud"
            fraud_label = 1
            will_return = True
        elif m_row["merchant_risk_score"] > 60 and random.random() < 0.25:
            fraud_type = "Merchant Fraud"
            fraud_label = 1
            will_return = True
        elif random.random() < 0.035:
            # Empty box
            will_return = True
            fraud_type = "Empty Box"
            fraud_label = 1
        elif random.random() < 0.03:
            # Bracketing abuse
            will_return = True
            fraud_type = "Bracketing Abuse"
            fraud_label = 1
        elif random.random() < 0.025:
            # Receipt fraud
            will_return = True
            fraud_type = "Receipt Fraud"
            fraud_label = 1
        elif random.random() < 0.02:
            # Fake INR
            will_return = True
            fraud_type = "Fake INR"
            fraud_label = 1
        elif random.random() < 0.015:
            # Price switching
            will_return = True
            fraud_type = "Price Switching"
            fraud_label = 1
        elif random.random() < 0.22:
            # Genuine normal return
            will_return = True
            fraud_type = "Legitimate"
            fraud_label = 0

        # Create return & refund if returned
        ret_weight = 0.0
        ret_reason = "Unknown/Not Returned"
        prod_cond = "Unknown/Not Returned"
        item_match = 1.0 if not will_return else 1.0

        if will_return:
            return_counter += 1
            ret_id = f"R{return_counter:05d}"
            ret_date = deliv_date + timedelta(days=random.randint(1, 14))

            # Weight and physical condition according to fraud typology
            if fraud_type == "Empty Box":
                ret_weight = round(orig_weight * random.uniform(0.02, 0.12), 2)
                item_match = 0.0
                prod_cond = "Missing"
                ret_reason = "Package arrived damaged"
            elif fraud_type == "Item Switching":
                ret_weight = round(orig_weight * random.uniform(0.40, 0.85), 2)
                item_match = 0.0
                prod_cond = "Good"
                ret_reason = "Wrong Item"
            elif fraud_type == "Wardrobing":
                ret_weight = orig_weight
                item_match = 1.0
                prod_cond = "Used"
                ret_reason = random.choice(["Size issue", "Changed mind"])
            elif fraud_type == "Fake INR":
                ret_weight = orig_weight
                item_match = 1.0
                prod_cond = "Good"
                ret_reason = "Item not received"
            elif fraud_type == "Price Switching":
                ret_weight = round(orig_weight * random.uniform(0.70, 0.95), 2)
                item_match = 0.0
                prod_cond = "Good"
                ret_reason = "Wrong Item"
            else:
                # Legitimate or standard return
                ret_weight = round(orig_weight * random.uniform(0.96, 1.04), 2)
                item_match = 1.0
                prod_cond = random.choice(["Good", "Good", "Defective"])
                ret_reason = random.choice(RETURN_REASONS)

            return_data.append({
                "return_id": ret_id,
                "order_id": order_id,
                "customer_id": cid,
                "return_date": ret_date.strftime("%Y-%m-%d"),
                "return_reason": ret_reason,
                "return_status": "Received",
                "returned_weight_kg": ret_weight,
                "product_condition": prod_cond,
                "item_match_flag": int(item_match),
                "packaging_condition": "Damaged" if is_tampered else "Intact"
            })

            # Create Refund
            refund_counter += 1
            ref_id = f"RF{refund_counter:05d}"
            ref_amt = order_amount
            ref_date = ret_date + timedelta(days=random.randint(1, 3))
            is_manual_review = 1 if (fraud_label == 1 or order_amount > 15000) else 0
            ref_status = "Pending" if is_manual_review else "Approved"

            refund_data.append({
                "refund_id": ref_id,
                "return_id": ret_id,
                "order_id": order_id,
                "refund_amount": ref_amt,
                "refund_date": ref_date.strftime("%Y-%m-%d"),
                "refund_status": ref_status,
                "refund_method": pay_method if pay_method in ["UPI", "Wallet", "Card"] else "Net Banking",
                "manual_review_flag": is_manual_review
            })

        # Calculate Training Feature Row
        # Simulating rolling customer statistics
        past_orders = customer_order_history[cid]
        c_order_cnt = len(past_orders)
        # Approximate return count
        if cid in serial_returners:
            c_ret_cnt = max(1, int(c_order_cnt * random.uniform(0.75, 0.95)))
        elif cid in wardrobers:
            c_ret_cnt = max(1, int(c_order_cnt * random.uniform(0.65, 0.85)))
        elif fraud_label == 1:
            c_ret_cnt = max(1, int(c_order_cnt * random.uniform(0.40, 0.75)))
        else:
            c_ret_cnt = int(c_order_cnt * random.uniform(0.0, 0.25))

        ret_rate = round((c_ret_cnt / max(1, c_order_cnt)) * 100.0, 1)
        ref_cnt = float(c_ret_cnt)
        ref_amt = round(c_ret_cnt * (order_amount * 0.9), 2)

        # Identity changes count
        if cid in sybil_group_1 or cid in sybil_group_2:
            addr_changes = random.randint(2, 5)
            phone_changes = random.randint(1, 4)
            dev_accounts = random.randint(3, 6)
        elif fraud_label == 1:
            addr_changes = random.randint(1, 3)
            phone_changes = random.randint(0, 2)
            dev_accounts = random.randint(2, 4)
        else:
            addr_changes = 0 if random.random() < 0.8 else 1
            phone_changes = 0 if random.random() < 0.9 else 1
            dev_accounts = 1 if random.random() < 0.85 else 2

        # Weight diff pct
        if will_return and orig_weight > 0:
            wt_diff_pct = round(((orig_weight - ret_weight) / orig_weight) * 100.0, 2)
        else:
            wt_diff_pct = 100.0 if not will_return else 0.0

        # Risk score calculation
        # Rule points + ML signal simulation
        score = 0
        if ret_rate > 65: score += 25
        elif ret_rate > 40: score += 12
        if addr_changes >= 2: score += 18
        if phone_changes >= 2: score += 15
        if dev_accounts >= 3: score += 20
        if wt_diff_pct > 30 and will_return: score += 25
        if item_match == 0.0: score += 25
        if c_row["previous_fraud_flag"] == 1: score += 20
        if is_chargeback: score += 25
        if prod_cond == "Used": score += 20
        if dp_row["partner_risk_score"] > 50: score += 10
        if m_row["merchant_risk_score"] > 50: score += 10
        if order_amount > 20000: score += 8

        # Genuine customer credit
        if fraud_label == 0 and c_row["account_age_days"] > 200:
            score = max(5, score - 20)

        # Bound score between 5 and 98
        score = min(98, max(5, score + random.randint(-5, 5)))

        if score >= 71:
            risk_level = "High"
            action = "Investigate"
        elif score >= 31:
            risk_level = "Medium"
            action = "Manual Review"
        else:
            risk_level = "Low"
            action = "Approve"

        fraud_eval_data.append({
            "order_id": order_id,
            "customer_id": cid,
            "order_amount": order_amount,
            "customer_order_count": c_order_cnt,
            "customer_return_count": float(c_ret_cnt),
            "return_rate": ret_rate,
            "refund_count": ref_cnt,
            "refund_amount": ref_amt,
            "address_changes": addr_changes,
            "phone_changes": phone_changes,
            "account_count": 1,
            "device_account_count": dev_accounts,
            "original_weight_kg": orig_weight,
            "returned_weight_kg": ret_weight,
            "weight_difference_pct": wt_diff_pct,
            "previous_fraud": c_row["previous_fraud_flag"],
            "chargeback_count": 1 if is_chargeback else 0,
            "merchant_return_rate": m_row["return_rate"],
            "delivery_partner_risk": dp_row["partner_risk_score"],
            "item_match_flag": item_match,
            "product_condition": prod_cond,
            "fraud_type": fraud_type,
            "fraud_label": fraud_label,
            "risk_score": score,
            "risk_level": risk_level,
            "recommended_action": action
        })

    # Device table
    # Group device records by customer and device
    df_identity_links = pd.DataFrame(identity_records)
    dev_grouped = df_identity_links.groupby(["customer_id", "device_id"]).size().reset_index(name="obs_count")
    dev_account_counts = df_identity_links.groupby("device_id")["customer_id"].nunique().to_dict()
    
    dev_table_rows = []
    for _, r in dev_grouped.iterrows():
        c_id = r["customer_id"]
        d_id = r["device_id"]
        dev_table_rows.append({
            "customer_id": c_id,
            "device_id": d_id,
            "first_seen_date": "2026-05-01",
            "last_seen_date": "2026-09-01",
            "account_count": dev_account_counts.get(d_id, 1)
        })
    df_devices = pd.DataFrame(dev_table_rows)

    df_orders = pd.DataFrame(order_data)
    df_payments = pd.DataFrame(payment_data)
    df_deliveries = pd.DataFrame(delivery_data)
    df_returns = pd.DataFrame(return_data)
    df_refunds = pd.DataFrame(refund_data)
    df_fraud_training = pd.DataFrame(fraud_eval_data)

    datasets = {
        "customers": df_customers,
        "merchants": df_merchants,
        "delivery_partners": df_delivery_partners,
        "orders": df_orders,
        "payments": df_payments,
        "deliveries": df_deliveries,
        "returns": df_returns,
        "refunds": df_refunds,
        "devices": df_devices,
        "identity_links": df_identity_links,
        "fraud_training_data": df_fraud_training
    }

    # Save to CSV files in output_dir
    for name, df in datasets.items():
        filepath = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(filepath, index=False)
        print(f"[Generator] Saved {len(df)} records -> {filepath}")

    print("[Generator] Synthetic benchmark dataset generated successfully.")
    return datasets


if __name__ == "__main__":
    generate_benchmark_dataset(n_orders=2500)
