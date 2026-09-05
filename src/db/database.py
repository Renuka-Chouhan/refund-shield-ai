"""
RefundShield AI - Database Module
Handles SQLite schema management, CSV ingestion, querying, and audit logging.
"""

import os
import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "refundshield.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sql", "schema.sql")
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    """Execute DDL schema to initialize all database tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized database at: {db_path}")


def ingest_csv_data(data_dir: str = WORKSPACE_DIR, db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Ingest CSV files into corresponding relational SQLite tables.
    Returns dictionary with counts of rows inserted per table.
    """
    conn = get_connection(db_path)
    table_files = {
        "customers": "customers.csv",
        "merchants": "merchants.csv",
        "delivery_partners": "delivery_partners.csv",
        "orders": "orders.csv",
        "payments": "payments.csv",
        "deliveries": "deliveries.csv",
        "returns": "returns.csv",
        "refunds": "refunds.csv",
        "devices": "devices.csv",
        "identity_links": "identity_links.csv"
    }

    inserted_counts = {}

    # Temporarily disable foreign key constraints during bulk loading
    conn.execute("PRAGMA foreign_keys = OFF;")

    for table_name, csv_filename in table_files.items():
        csv_path = os.path.join(data_dir, csv_filename)
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Clean column names
            df.columns = [col.strip() for col in df.columns]
            
            # Replace existing content
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            inserted_counts[table_name] = len(df)
            print(f"[DB] Ingested {len(df)} rows into '{table_name}' from {csv_filename}")
        else:
            print(f"[DB] Warning: File not found: {csv_path}")

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()
    return inserted_counts


def run_query(query: str, db_path: str = DB_PATH, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute a SQL query and return results as a Pandas DataFrame."""
    conn = get_connection(db_path)
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def log_fraud_evaluation(
    eval_id: str,
    order_id: str,
    customer_id: str,
    rule_score: float,
    ml_prob: float,
    hybrid_score: float,
    risk_level: str,
    action: str,
    fraud_type: str,
    rules_json: str,
    db_path: str = DB_PATH
) -> None:
    """Persist a single fraud evaluation result to the audit log table."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO fraud_evaluations 
        (evaluation_id, order_id, customer_id, rule_score, ml_probability, 
         hybrid_risk_score, risk_level, recommended_action, predicted_fraud_type, triggered_rules_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (eval_id, order_id, customer_id, rule_score, ml_prob, hybrid_score, risk_level, action, fraud_type, rules_json))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("[DB] Running DB setup and ingestion...")
    initialize_database()
    counts = ingest_csv_data()
    print("[DB] Ingestion complete. Summary of tables loaded:")
    for tbl, cnt in counts.items():
        print(f"  - {tbl}: {cnt} rows")

    test_df = run_query("SELECT COUNT(*) AS total_orders FROM orders;")
    print("[DB] Sanity check order count:", test_df['total_orders'].iloc[0])
