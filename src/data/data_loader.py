"""
RefundShield AI - Data Loader Module
Loads, validates, and merges relational tables into comprehensive analytical views.
Supports loading from raw CSVs (seed or benchmark) and SQLite database.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DATA_DIR = os.path.join(ROOT_DIR, "data", "processed")
DB_PATH = os.path.join(ROOT_DIR, "data", "refundshield.db")


def load_raw_tables(source_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV tables from specified directory.
    Defaults to PROCESSED_DATA_DIR if available, else ROOT_DIR (seed data).
    """
    if source_dir is None:
        if os.path.exists(os.path.join(PROCESSED_DATA_DIR, "orders.csv")):
            source_dir = PROCESSED_DATA_DIR
        else:
            source_dir = ROOT_DIR

    table_names = [
        "customers", "merchants", "delivery_partners", "orders",
        "payments", "deliveries", "returns", "refunds", "devices",
        "identity_links", "fraud_training_data"
    ]

    tables = {}
    for name in table_names:
        csv_path = os.path.join(source_dir, f"{name}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df.columns = [c.strip() for c in df.columns]
            tables[name] = df
        else:
            # Fallback to root directory if not in processed
            alt_path = os.path.join(ROOT_DIR, f"{name}.csv")
            if os.path.exists(alt_path):
                df = pd.read_csv(alt_path)
                df.columns = [c.strip() for c in df.columns]
                tables[name] = df
            else:
                tables[name] = pd.DataFrame()

    return tables


def load_from_sqlite(db_path: str = DB_PATH) -> Dict[str, pd.DataFrame]:
    """Load tables from SQLite database."""
    conn = sqlite3.connect(db_path)
    tables = {}
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
    
    for tbl in table_names:
        tables[tbl] = pd.read_sql_query(f"SELECT * FROM {tbl};", conn)
    conn.close()
    return tables


def get_merged_master_data(tables: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    """
    Produces a master joined DataFrame joining:
    Orders + Customers + Merchants + Delivery Partners + Deliveries + Returns + Refunds + Payments.
    """
    if tables is None:
        tables = load_raw_tables()

    df_orders = tables.get("orders", pd.DataFrame()).copy()
    if df_orders.empty:
        raise ValueError("Orders table is empty or missing.")

    # Merge Customers
    df_customers = tables.get("customers", pd.DataFrame())
    if not df_customers.empty:
        df_orders = df_orders.merge(df_customers, on="customer_id", how="left")

    # Merge Merchants
    df_merchants = tables.get("merchants", pd.DataFrame())
    if not df_merchants.empty:
        m_renamed = df_merchants.rename(columns={
            "category": "merchant_category",
            "return_rate": "merchant_return_rate",
            "refund_rate": "merchant_refund_rate",
            "fraud_rate": "merchant_fraud_rate",
            "total_orders": "merchant_total_orders"
        })
        df_orders = df_orders.merge(m_renamed, on="merchant_id", how="left")

    # Merge Payments
    df_payments = tables.get("payments", pd.DataFrame())
    if not df_payments.empty:
        pay_cols = [c for c in df_payments.columns if c != "payment_id"]
        df_orders = df_orders.merge(df_payments[pay_cols], on="order_id", how="left")

    # Merge Deliveries
    df_deliveries = tables.get("deliveries", pd.DataFrame())
    if not df_deliveries.empty:
        df_orders = df_orders.merge(df_deliveries, on="order_id", how="left")

    # Merge Delivery Partners
    df_dp = tables.get("delivery_partners", pd.DataFrame())
    if not df_dp.empty:
        dp_renamed = df_dp.rename(columns={
            "total_deliveries": "dp_total_deliveries",
            "return_complaints": "dp_return_complaints",
            "tampering_cases": "dp_tampering_cases",
            "suspicious_returns": "dp_suspicious_returns",
            "partner_risk_score": "delivery_partner_risk"
        })
        df_orders = df_orders.merge(dp_renamed, on="delivery_partner_id", how="left")

    # Merge Returns
    df_returns = tables.get("returns", pd.DataFrame())
    if not df_returns.empty:
        df_orders = df_orders.merge(df_returns, on=["order_id", "customer_id"], how="left")

    # Merge Refunds
    df_refunds = tables.get("refunds", pd.DataFrame())
    if not df_refunds.empty:
        ref_cols = [c for c in df_refunds.columns if c != "return_id"]
        df_orders = df_orders.merge(df_refunds[ref_cols], on="order_id", how="left")

    return df_orders


if __name__ == "__main__":
    t = load_raw_tables()
    print("[DataLoader] Loaded tables:", list(t.keys()))
    master = get_merged_master_data(t)
    print(f"[DataLoader] Master merged view: {master.shape[0]} rows, {master.shape[1]} columns")
