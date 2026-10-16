# 🛡️ RefundShield AI – AI-Powered E-Commerce Refund & Return Fraud Detection System

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Render Live](https://img.shields.io/badge/Render-Live%20Demo-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://refundshield-ai.onrender.com/)
[![Swagger API](https://img.shields.io/badge/OpenAPI-Swagger%20Docs-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](https://refundshield-ai.onrender.com/docs)
[![XGBoost](https://img.shields.io/badge/XGBoost-Models-EB6100?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)

**RefundShield AI** is an industry-grade, explainable, multi-layer fraud detection platform engineered to protect e-commerce enterprises and payment platforms against repeated, distributed, and coordinated refund and return fraud.

Unlike conventional payment fraud systems that examine single checkout swipes in isolation, RefundShield AI correlates **historical shopping cadence, identity mutation velocity, hardware device fingerprints, physical package return telemetry, carrier route tampering, and merchant-side anomalies**.

---

## 📌 Problem Statement & 12+ Fraud Typologies

E-commerce companies lose tens of billions annually to return abuse. RefundShield AI explicitly detects and categorizes:

1. **Wardrobing**: Ordering fashion, wearing for an event, and returning with minor wear or detached tags.
2. **Item Switching**: Returning a cheaper, damaged, or counterfeit item inside the genuine product packaging.
3. **Empty Box Returns**: Dramatic package weight loss where goods are stripped before return pickup.
4. **Serial Returning**: Extreme return-to-order ratio (>65%) across repeated purchasing cycles.
5. **Bracketing Abuse**: Ordering 4–6 variations/sizes of a single item and returning 100% of them.
6. **Stolen Merchandise Returns**: Returning stolen or unverified items for refund payouts.
7. **Price Switching**: Returning a lower-tier product claiming the refund for an expensive sibling SKU.
8. **Receipt Fraud**: Manipulated receipt IDs, duplicate return requests across transaction keys.
9. **Chargeback / Friendly Fraud**: Customer receives goods/refund and files an unauthorized payment dispute with their bank.
10. **Fake "Item Not Received" (INR)**: Falsely claiming shipping failure despite carrier confirmation.
11. **Identity & Account Manipulation**: Rapid mutation of addresses, phone hashes, and email aliases.
12. **Multiple-Account Sybil Rings**: Shared hardware device fingerprints linking ostensibly independent accounts.
13. **Delivery Courier Tampering**: Delivery personnel collusion and in-transit package tampering.
14. **Merchant-Side Leakage**: Rogue merchant employees and abnormal refund rates.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────┐
                               │  E-Commerce Transaction Event  │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │  Relational Database Ingestion   │
                              │       (SQLite / PostgreSQL)      │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │   Multi-Entity Feature Pipeline  │
                              │   (25+ Domain & Velocity Signals)│
                              └───────┬──────────────┬───────────┘
                                      │              │
                    ┌─────────────────┘              └──────────────────┐
                    ▼                                                   ▼
         ┌─────────────────────┐                             ┌─────────────────────┐
         │  Rule-Based Engine  │                             │ Machine Learning    │
         │  14+ Business Rules │                             │ XGBoost & RF Models │
         │  Points [0 – 100]   │                             │ Probability [0 – 1] │
         └──────────┬──────────┘                             └──────────┬──────────┘
                    │                                                   │
                    └─────────────────┬─────────────────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Identity Graph Network    │
                        │ Multi-Account Sybil Rings │
                        │ Penalty [0 – 30 pts]      │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Hybrid Decision Engine    │
                        │ Risk Score 0 – 100        │
                        │ Typology Classification   │
                        └─────────────┬─────────────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               ▼                      ▼                      ▼
         Low Risk (0–30)      Medium Risk (31–70)    High Risk (71–100)
            [Approve]           [Manual Review]     [Investigate/Block]
               │                      │                      │
               └──────────────────────┼──────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Explainability Core      │
                        │  Audit Reasons & Log      │
                        └─────────────┬─────────────┘
                                      │
                      ┌───────────────┴───────────────┐
                      ▼                               ▼
          ┌───────────────────────┐       ┌───────────────────────┐
          │  Streamlit Command    │       │  Power BI Enterprise  │
          │  Center & Sandbox     │       │  Star Schema Model    │
          └───────────────────────┘       └───────────────────────┘
```

---

## 🎯 Risk Classification & Tiers

| Score Range | Risk Level | Action | Operational Workflow |
| :--- | :--- | :--- | :--- |
| **0 – 30** | **Low Risk** | `Approve` | Automated instant refund processing to original payment source. |
| **31 – 70** | **Medium Risk** | `Manual Review` | Queued for fraud analyst inspection; payout held for verification. |
| **71 – 100** | **High Risk** | `Investigate / Block` | Automated return block, physical warehouse inspection, account suspension. |

---

## 📂 Project Repository Structure

```
RefundShield_Dataset/
├── app.py                         # Interactive Streamlit Web Command Center & Live Simulator
├── README.md                      # Primary project documentation
├── ARCHITECTURE.md                # In-depth technical architecture blueprint
├── sql/
│   ├── schema.sql                 # DDL relational schema for SQLite / PostgreSQL
│   └── analytics_queries.sql      # 10+ industry analytical SQL queries for fraud investigators
├── src/
│   ├── db/
│   │   └── database.py            # SQLite database manager, CSV ingestion, audit logger
│   ├── data/
│   │   ├── dataset_generator.py   # Realistic benchmark generator (2,500+ records, all 12 fraud types)
│   │   ├── data_loader.py         # Multi-source relational table loader & joiner
│   │   └── feature_engineering.py # 25+ domain features extractor & inference vector builder
│   ├── rules/
│   │   └── rule_engine.py         # Configurable 14-rule scoring engine with transparent point audits
│   ├── models/
│   │   ├── train_models.py        # Supervised Random Forest & XGBoost training pipeline
│   │   ├── fraud_type_classifier.py # Multi-class typology classifier (93% accuracy)
│   │   └── evaluator.py           # Publication-quality ROC, PR, feature importance charts
│   ├── graph/
│   │   └── network_analyzer.py    # NetworkX identity graph engine & Sybil ring detector
│   └── scoring/
│       └── hybrid_engine.py       # Unified scoring orchestrator combining Rules, ML, and Graph
├── reports/
│   └── figures/                   # Generated evaluation plots (roc_curve.png, confusion_matrix.png, etc.)
└── saved_models/                  # Serialized XGBoost, Random Forest, and typology models
```

---

```

---

## ⚡ Real-Time Dynamic FastAPI Platform & Web Dashboard

RefundShield AI is equipped with an enterprise-grade **FastAPI REST API** with live sub-millisecond dynamic relational queries and an interactive dark glassmorphic command center dashboard.

### 🌐 Key Features & Endpoints
- **Dynamic Customer 360 Dossier (`GET /api/customers/{customer_id}`)**:
  - Dynamically fetches complete profile, full transaction history, return reasons, weight discrepancies, and linked hardware devices.
  - Computes real-time **Hybrid Risk Score (0–100)** combining XGBoost ML inference, 14 business rules, and NetworkX identity graph penalties with point-by-point explainability.
- **Dynamic Order Risk Inspection (`GET /api/orders/{order_id}`)**:
  - Fetches multi-table relational context across order, carrier tampering, merchant risk, physical weight loss %, and item SKU matching.
- **Real-Time Transaction Evaluation Sandbox (`POST /api/evaluate`)**:
  - Evaluates custom transactions or auto-populates historical baseline from `customer_id`.
- **Instant Global Search & Autocomplete (`GET /api/search?q=...`)**:
  - Sub-second autocomplete search across Customers (`C0001`–`C0450`), Orders, Devices, and Phone Hashes.
- **Executive Analytics & Supply Chain (`GET /api/analytics/...`)**:
  - KPIs, Risk Tier Distribution, Fraud Typology Exposure, and Carrier Tampering rankings.
- **Interactive OpenAPI Documentation**:
  - Interactive Swagger UI at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

---

## 🚀 Quick Start Guide

### 1. Ingest Full Dataset & Initialize Database
```bash
python -c "from src.db.database import ingest_csv_data, initialize_database; initialize_database(); ingest_csv_data(data_dir='data/processed')"
```

### 2. Launch the Dynamic FastAPI Platform & Web UI (Recommended)
```bash
python main.py
# Or run with uvicorn directly:
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- **Live Cloud Deployment**: [https://refundshield-ai.onrender.com](https://refundshield-ai.onrender.com)
- **Local Web Command Center**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Interactive Swagger API Documentation**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Example cURL / API Usage

**Dynamic Customer Dossier:**
```bash
curl -X GET "http://127.0.0.1:8000/api/customers/C0022"
```

**Real-Time Transaction Evaluation:**
```bash
curl -X POST "http://127.0.0.1:8000/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C0022",
    "order_amount": 28500,
    "category": "Electronics",
    "original_weight_kg": 3.2,
    "returned_weight_kg": 0.4,
    "item_match_flag": 0.0,
    "product_condition": "Missing",
    "return_reason": "Wrong Item"
  }'
```

---

## 📈 Model Performance Highlights

- **XGBoost Classifier**: Stratified 5-Fold Cross-Validation ROC-AUC $> 0.99$, PR-AUC $> 0.99$.
- **Random Forest Classifier**: F1-Score: $1.00$ on benchmark validation set.
- **Multi-Class Typology Classifier**: $93\%$ multi-class accuracy across all 13 distinct fraud and legitimate categories.
- **Top Predictive Features**:
  1. `return_rate` (Customer long-term return ratio)
  2. `customer_return_count` (Absolute return volume)
  3. `refund_count` (Prior refund frequency)
  4. `device_account_count` (Hardware sharing / Sybil accounts)
  5. `returned_weight_kg` & `weight_difference_pct` (Empty box & item switching telemetry)
  6. `chargeback_count` (Friendly fraud dispute history)

---

## 🏆 Business Impact & ROI

- **Fraud Loss Intercepted**: In benchmark evaluation, RefundShield AI withheld over **Rs. 14,000,000** in suspicious refund claims.
- **Operational Optimization**: Filtered out **92%** of low-risk returns for instant automated approval, allowing human fraud analysts to focus exclusively on the high-risk and medium-risk queues.
- **Sybil Ring Interception**: Discovered coordinated multi-account clusters sharing devices and addresses before refund disbursement.
