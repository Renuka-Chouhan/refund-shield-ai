# RefundShield AI – System Architecture & Technical Specifications

## 1. Executive Summary

**RefundShield AI** is an enterprise-grade, multi-layer fraud detection platform designed to detect repeated, distributed, and coordinated refund and return abuse across e-commerce and payment platforms.

Rather than treating each refund request in isolation, RefundShield AI correlates:
- **Historical customer behavior** (return-to-order ratio, refund cadence, CLV)
- **Identity signals** (device fingerprints, phone mutations, address velocity)
- **Physical inspection telemetry** (outbound vs returned package weight, item mismatch flags, packaging integrity)
- **Third-party courier risk** (tampering incidents, delivery route discrepancies)
- **Merchant-side anomalies** (unusual return spikes, unauthorized refund leakage)
- **Payment & banking disputes** (chargebacks, payment attempt velocity)

---

## 2. Multi-Layer Hybrid Architecture

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

## 3. Hybrid Scoring Formula

The final **Hybrid Fraud Risk Score** is calculated as a weighted ensemble:

$$\text{Hybrid Risk Score} = \text{clamp}\Big(\big(w_{\text{rule}} \times \text{RuleScore}\big) + \big(w_{\text{ml}} \times (\text{ML\_Probability} \times 100)\big) + \big(w_{\text{net}} \times \text{NetworkPenalty} \times 3.33\big), \; 0, \; 100\Big)$$

### Default Weights:
- $w_{\text{rule}} = 0.40$ (Deterministic business policies, regulatory checks)
- $w_{\text{ml}} = 0.45$ (Statistical non-linear behavioral anomaly detection)
- $w_{\text{net}} = 0.15$ (Sybil account ring & shared entity multiplier)

### Critical Fraud Overrides:
If hard physical evidence is detected (e.g., package weight deficit $\ge 50\%$ or inspection item mismatch flag $= 0$), the hybrid engine applies a hard floor of $\ge 78$, ensuring critical fraud cannot be bypassed by ML false negatives.

---

## 4. Entity-Relationship Data Model

```
CUSTOMERS (1) ────< ORDERS (M) >──── (1) MERCHANTS
                       │
                       ├──── (1) PAYMENTS
                       ├──── (1) DELIVERIES >──── (1) DELIVERY_PARTNERS
                       ├──── (1) RETURNS ──── (1) REFUNDS
                       │
CUSTOMERS (1) ────< IDENTITY_LINKS (M) >──── (1) DEVICES
```

### Relational Tables:
1. **`customers`**: Demographic, tenure, previous fraud flags, and account status.
2. **`merchants`**: Historical order counts, category return rates, and risk indices.
3. **`delivery_partners`**: Courier delivery volume, tampering complaints, and route risk scores.
4. **`orders`**: Transaction amounts, SKUs, discounts, and order timestamps.
5. **`payments`**: Payment methods, success statuses, chargeback flags, and retry attempts.
6. **`deliveries`**: Original measured package weight, carrier assignment, and tampering flags.
7. **`returns`**: Return reasons, return status, physical returned package weight, and item match flag.
8. **`refunds`**: Refund amount, payout method, approval status, and manual review flags.
9. **`devices`**: First/last seen dates, hardware fingerprints, and concurrent account count.
10. **`identity_links`**: Cross-entity graph table linking customer, device, phone hash, and address.
11. **`fraud_evaluations`**: Audit log recording every decision, rule breakdown, and ML score.

---

## 5. NetworkX Identity Graph Schema

- **Nodes**:
  - `Customer` (attribute: `is_fraud`)
  - `Device` (attribute: `device_id`)
  - `Phone` (attribute: `phone_hash`)
  - `Address` (attribute: `address_id`)
  - `PaymentFingerprint` (attribute: `fingerprint_id`)
- **Edges**:
  - `Customer` ──`USES_DEVICE`──> `Device`
  - `Customer` ──`USES_PHONE`──> `Phone`
  - `Customer` ──`SHIPS_TO`──> `Address`
  - `Customer` ──`PAYS_WITH`──> `PaymentFingerprint`
- **Graph Algorithms**:
  - **Connected Components**: Groups entities into connected clusters. Any cluster with $\ge 2$ customers is flagged as a potential Sybil ring.
  - **Neighbor Risk Propagation**: Evaluates what percentage of linked accounts in the ring have confirmed fraud histories.
