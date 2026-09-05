"""
RefundShield AI - Power BI Star Schema Data Exporter
Transforms relational transactional data into a Star / Snowflake Dimensional Model 
optimized for Power BI Business Intelligence, DAX measures, and drilldown reporting.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

from src.data.data_loader import load_raw_tables

POWER_BI_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "power_bi", "data")
os.makedirs(POWER_BI_DATA_DIR, exist_ok=True)


def export_powerbi_model():
    """
    Exports clean, dimensional CSV files for direct import into Power BI:
    1. Dim_Customer
    2. Dim_Merchant
    3. Dim_DeliveryPartner
    4. Dim_Date
    5. Fact_Orders
    6. Fact_Returns_Refunds
    7. Bridge_IdentityNetwork
    """
    print("[PowerBI Export] Loading master tables...")
    tables = load_raw_tables()

    df_customers = tables.get("customers", pd.DataFrame())
    df_merchants = tables.get("merchants", pd.DataFrame())
    df_dp = tables.get("delivery_partners", pd.DataFrame())
    df_orders = tables.get("orders", pd.DataFrame())
    df_payments = tables.get("payments", pd.DataFrame())
    df_deliveries = tables.get("deliveries", pd.DataFrame())
    df_returns = tables.get("returns", pd.DataFrame())
    df_refunds = tables.get("refunds", pd.DataFrame())
    df_identity = tables.get("identity_links", pd.DataFrame())
    df_evals = tables.get("fraud_training_data", pd.DataFrame())

    # 1. Dim_Customer
    dim_customer = df_customers.copy()
    dim_customer["Customer_Segment"] = np.where(
        dim_customer["previous_fraud_flag"] == 1, "High Risk / Flagged",
        np.where(dim_customer["account_age_days"] >= 365, "Loyal Veteran", "Standard Shopper")
    )
    dim_customer.to_csv(os.path.join(POWER_BI_DATA_DIR, "Dim_Customer.csv"), index=False)
    print(f"  -> Exported Dim_Customer ({len(dim_customer)} rows)")

    # 2. Dim_Merchant
    dim_merchant = df_merchants.copy()
    dim_merchant["Merchant_Risk_Tier"] = np.where(
        dim_merchant["merchant_risk_score"] >= 50, "High Risk",
        np.where(dim_merchant["merchant_risk_score"] >= 30, "Medium Risk", "Low Risk")
    )
    dim_merchant.to_csv(os.path.join(POWER_BI_DATA_DIR, "Dim_Merchant.csv"), index=False)
    print(f"  -> Exported Dim_Merchant ({len(dim_merchant)} rows)")

    # 3. Dim_DeliveryPartner
    dim_dp = df_dp.copy()
    dim_dp["Partner_Risk_Tier"] = np.where(
        dim_dp["partner_risk_score"] >= 50, "High Tampering Risk",
        np.where(dim_dp["partner_risk_score"] >= 30, "Moderate Risk", "Reliable Carrier")
    )
    dim_dp.to_csv(os.path.join(POWER_BI_DATA_DIR, "Dim_DeliveryPartner.csv"), index=False)
    print(f"  -> Exported Dim_DeliveryPartner ({len(dim_dp)} rows)")

    # 4. Dim_Date (Covering order dates)
    order_dates = pd.to_datetime(df_orders["order_date"].dropna().unique())
    min_date = order_dates.min()
    max_date = order_dates.max() + pd.Timedelta(days=45)
    all_dates = pd.date_range(start=min_date, end=max_date)

    dim_date = pd.DataFrame({
        "Date": all_dates,
        "Date_Key": all_dates.strftime("%Y%m%d").astype(int),
        "Year": all_dates.year,
        "Quarter": "Q" + all_dates.quarter.astype(str),
        "Month": all_dates.strftime("%b"),
        "Month_Number": all_dates.month,
        "Day": all_dates.day,
        "Day_Name": all_dates.strftime("%A"),
        "Is_Weekend": (all_dates.dayofweek >= 5).astype(int)
    })
    dim_date.to_csv(os.path.join(POWER_BI_DATA_DIR, "Dim_Date.csv"), index=False)
    print(f"  -> Exported Dim_Date ({len(dim_date)} rows)")

    # 5. Fact_Orders (Central Fact Table)
    fact_orders = df_orders.merge(df_payments, on="order_id", how="left")
    fact_orders = fact_orders.merge(df_deliveries, on="order_id", how="left")
    
    # Merge fraud score if available
    if not df_evals.empty:
        score_cols = df_evals[["order_id", "risk_score", "risk_level", "fraud_type", "fraud_label", "recommended_action"]].drop_duplicates(subset=["order_id"])
        fact_orders = fact_orders.merge(score_cols, on="order_id", how="left")
    else:
        fact_orders["risk_score"] = 25
        fact_orders["risk_level"] = "Low"
        fact_orders["fraud_type"] = "Legitimate"
        fact_orders["fraud_label"] = 0
        fact_orders["recommended_action"] = "Approve"

    fact_orders["Has_Return"] = fact_orders["order_id"].isin(df_returns["order_id"]).astype(int)
    fact_orders.to_csv(os.path.join(POWER_BI_DATA_DIR, "Fact_Orders.csv"), index=False)
    print(f"  -> Exported Fact_Orders ({len(fact_orders)} rows)")

    # 6. Fact_Returns_Refunds
    fact_returns = df_returns.merge(df_refunds, on=["return_id", "order_id"], how="left")
    fact_returns = fact_returns.merge(df_deliveries[["order_id", "original_weight_kg", "delivery_partner_id"]], on="order_id", how="left")
    fact_returns["Weight_Difference_Kg"] = fact_returns["original_weight_kg"] - fact_returns["returned_weight_kg"]
    fact_returns["Weight_Difference_Pct"] = np.where(
        fact_returns["original_weight_kg"] > 0,
        ((fact_returns["Weight_Difference_Kg"] / fact_returns["original_weight_kg"]) * 100.0).round(2),
        0.0
    )
    fact_returns.to_csv(os.path.join(POWER_BI_DATA_DIR, "Fact_Returns_Refunds.csv"), index=False)
    print(f"  -> Exported Fact_Returns_Refunds ({len(fact_returns)} rows)")

    # 7. Bridge_IdentityNetwork
    bridge_identity = df_identity.copy()
    bridge_identity.to_csv(os.path.join(POWER_BI_DATA_DIR, "Bridge_IdentityNetwork.csv"), index=False)
    print(f"  -> Exported Bridge_IdentityNetwork ({len(bridge_identity)} rows)")

    print(f"\n[PowerBI Export] All 7 Star Schema files successfully saved to: {POWER_BI_DATA_DIR}")


if __name__ == "__main__":
    export_powerbi_model()
