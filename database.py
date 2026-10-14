"""
RefundShield AI - Database Engine & Session Management Module
Supports both local development (SQLite) and production cloud clusters (PostgreSQL).
Includes automatic schema creation, connection pooling, and CSV dataset auto-seeding.
"""

import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models import (
    Base,
    Customer,
    Merchant,
    DeliveryPartner,
    Order,
    Payment,
    Delivery,
    Return,
    Refund,
    Device,
    IdentityLink
)

# Resolve Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "refundshield.db")
os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)

# Environment DATABASE_URL (for Render, Railway, AWS RDS, or SQLite local)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Fix Heroku/Render legacy postgres:// URI schema for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure Connection Engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # Production PostgreSQL pool configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=15,
        max_overflow=25,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_schema():
    """Creates all relational tables and indices if not present."""
    Base.metadata.create_all(bind=engine)
    print("[DB] Relational schema and indices initialized.")


def seed_database_if_empty():
    """
    Auto-seeds all 10 relational tables from benchmark CSVs if the database is newly initialized.
    Ensures seamless zero-config cloud deployment on platforms like Render or Railway.
    """
    initialize_schema()
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        has_customers = db.query(Customer).first() is not None
        if has_customers:
            print("[DB] Database already populated. Skipping seeder.")
            return

        print("[DB] Empty database detected. Ingesting benchmark CSV datasets...")

        # Locate CSV source directory (check data/processed first, then root)
        processed_dir = os.path.join(BASE_DIR, "data", "processed")
        data_dir = processed_dir if os.path.exists(os.path.join(processed_dir, "orders.csv")) else BASE_DIR

        def read_csv(filename):
            p = os.path.join(data_dir, filename)
            if not os.path.exists(p):
                p = os.path.join(BASE_DIR, filename)
            if os.path.exists(p):
                df = pd.read_csv(p)
                df.columns = [c.strip() for c in df.columns]
                return df
            return pd.DataFrame()

        # 1. Customers
        df_cust = read_csv("customers.csv")
        if not df_cust.empty:
            for _, r in df_cust.iterrows():
                db.add(Customer(
                    customer_id=str(r["customer_id"]).strip(),
                    account_age_days=int(r["account_age_days"]),
                    registration_date=datetime.strptime(str(r["registration_date"]).strip(), "%Y-%m-%d").date(),
                    gender=str(r.get("gender", "N/A")),
                    city=str(r["city"]).strip(),
                    previous_fraud_flag=int(r.get("previous_fraud_flag", 0)),
                    account_status=str(r.get("account_status", "Active")).strip()
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_cust)} customers.")

        # 2. Merchants
        df_merch = read_csv("merchants.csv")
        if not df_merch.empty:
            for _, r in df_merch.iterrows():
                db.add(Merchant(
                    merchant_id=str(r["merchant_id"]).strip(),
                    category=str(r.get("category", "General")),
                    total_orders=int(r.get("total_orders", 0)),
                    return_rate=float(r.get("return_rate", 0.0)),
                    refund_rate=float(r.get("refund_rate", 0.0)),
                    fraud_rate=float(r.get("fraud_rate", 0.0)),
                    merchant_risk_score=int(r.get("merchant_risk_score", 0))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_merch)} merchants.")

        # 3. Delivery Partners
        df_dp = read_csv("delivery_partners.csv")
        if not df_dp.empty:
            for _, r in df_dp.iterrows():
                db.add(DeliveryPartner(
                    delivery_partner_id=str(r["delivery_partner_id"]).strip(),
                    total_deliveries=int(r.get("total_deliveries", 0)),
                    return_complaints=int(r.get("return_complaints", 0)),
                    tampering_cases=int(r.get("tampering_cases", 0)),
                    suspicious_returns=int(r.get("suspicious_returns", 0)),
                    partner_risk_score=int(r.get("partner_risk_score", 0))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_dp)} delivery partners.")

        # 4. Orders
        df_orders = read_csv("orders.csv")
        if not df_orders.empty:
            for _, r in df_orders.iterrows():
                db.add(Order(
                    order_id=str(r["order_id"]).strip(),
                    customer_id=str(r["customer_id"]).strip(),
                    merchant_id=str(r["merchant_id"]).strip(),
                    product_id=str(r.get("product_id", "PROD_001")).strip(),
                    category=str(r["category"]).strip(),
                    order_amount=float(r["order_amount"]),
                    order_date=datetime.strptime(str(r["order_date"]).strip(), "%Y-%m-%d").date(),
                    quantity=int(r.get("quantity", 1)),
                    discount_amount=float(r.get("discount_amount", 0.0)),
                    payment_id=str(r.get("payment_id", ""))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_orders)} orders.")

        # 5. Payments
        df_pay = read_csv("payments.csv")
        if not df_pay.empty:
            for _, r in df_pay.iterrows():
                db.add(Payment(
                    payment_id=str(r["payment_id"]).strip(),
                    order_id=str(r["order_id"]).strip(),
                    payment_method=str(r["payment_method"]).strip(),
                    payment_amount=float(r["payment_amount"]),
                    payment_status=str(r.get("payment_status", "Success")).strip(),
                    chargeback_flag=int(r.get("chargeback_flag", 0)),
                    chargeback_amount=float(r.get("chargeback_amount", 0.0)),
                    payment_attempts=int(r.get("payment_attempts", 1))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_pay)} payments.")

        # 6. Deliveries
        df_del = read_csv("deliveries.csv")
        if not df_del.empty:
            for _, r in df_del.iterrows():
                db.add(Delivery(
                    delivery_id=str(r["delivery_id"]).strip(),
                    order_id=str(r["order_id"]).strip(),
                    delivery_partner_id=str(r["delivery_partner_id"]).strip(),
                    delivery_date=datetime.strptime(str(r["delivery_date"]).strip(), "%Y-%m-%d").date(),
                    delivery_status=str(r.get("delivery_status", "Delivered")).strip(),
                    original_weight_kg=float(r["original_weight_kg"]),
                    package_tampered=int(r.get("package_tampered", 0)),
                    delivery_location_id=str(r.get("delivery_location_id", ""))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_del)} deliveries.")

        # 7. Returns
        df_ret = read_csv("returns.csv")
        if not df_ret.empty:
            for _, r in df_ret.iterrows():
                db.add(Return(
                    return_id=str(r["return_id"]).strip(),
                    order_id=str(r["order_id"]).strip(),
                    customer_id=str(r["customer_id"]).strip(),
                    return_date=datetime.strptime(str(r["return_date"]).strip(), "%Y-%m-%d").date(),
                    return_reason=str(r.get("return_reason", "")),
                    return_status=str(r.get("return_status", "Received")).strip(),
                    returned_weight_kg=float(r["returned_weight_kg"]),
                    product_condition=str(r.get("product_condition", "Good")).strip(),
                    item_match_flag=int(r.get("item_match_flag", 1)),
                    packaging_condition=str(r.get("packaging_condition", "Intact")).strip()
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_ret)} returns.")

        # 8. Refunds
        df_ref = read_csv("refunds.csv")
        if not df_ref.empty:
            for _, r in df_ref.iterrows():
                db.add(Refund(
                    refund_id=str(r["refund_id"]).strip(),
                    return_id=str(r["return_id"]).strip(),
                    order_id=str(r["order_id"]).strip(),
                    refund_amount=float(r["refund_amount"]),
                    refund_date=datetime.strptime(str(r["refund_date"]).strip(), "%Y-%m-%d").date(),
                    refund_status=str(r.get("refund_status", "Approved")).strip(),
                    refund_method=str(r.get("refund_method", "Original Source")).strip(),
                    manual_review_flag=int(r.get("manual_review_flag", 0))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_ref)} refunds.")

        # 9. Devices
        df_dev = read_csv("devices.csv")
        if not df_dev.empty:
            for _, r in df_dev.iterrows():
                db.merge(Device(
                    customer_id=str(r["customer_id"]).strip(),
                    device_id=str(r["device_id"]).strip(),
                    first_seen_date=datetime.strptime(str(r["first_seen_date"]).strip(), "%Y-%m-%d").date() if "first_seen_date" in r and pd.notna(r["first_seen_date"]) else None,
                    last_seen_date=datetime.strptime(str(r["last_seen_date"]).strip(), "%Y-%m-%d").date() if "last_seen_date" in r and pd.notna(r["last_seen_date"]) else None,
                    account_count=int(r.get("account_count", 1))
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_dev)} devices.")

        # 10. Identity Links
        df_links = read_csv("identity_links.csv")
        if not df_links.empty:
            for _, r in df_links.iterrows():
                db.add(IdentityLink(
                    customer_id=str(r["customer_id"]).strip(),
                    address_id=str(r.get("address_id", "")).strip(),
                    phone_hash=str(r.get("phone_hash", "")).strip(),
                    device_id=str(r.get("device_id", "")).strip(),
                    payment_fingerprint=str(r.get("payment_fingerprint", "")).strip()
                ))
            db.commit()
            print(f"[DB] Seeded {len(df_links)} identity links.")

        print("[DB] All 10 benchmark datasets seeded successfully into relational database.")

    except Exception as e:
        db.rollback()
        print(f"[DB Error] Failed to seed database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database_if_empty()
