# RefundShield AI – Enterprise Power BI Dashboard Guide

This guide provides step-by-step instructions for importing, modeling, and designing the **RefundShield AI Power BI Dashboard**.

---

## 1. Data Model Architecture (Star Schema)

The exported datasets in [`power_bi/data/`](file:///c:/Users/asus/Downloads/RefundShield_Dataset/power_bi/data) form a production-grade Star / Snowflake Dimensional Model:

```
                  ┌──────────────────┐
                  │   Dim_Customer   │
                  └────────┬─────────┘
                           │ 1
                           │
                           │ *
┌──────────────────┐  *    ▼     *   ┌────────────────────────┐
│   Dim_Merchant   │◄── Fact_Orders ──►│ Dim_DeliveryPartner    │
└──────────────────┘   (Central Fact)└────────────────────────┘
                           │ 1
                           │
                           │ *
                           ▼
                  ┌──────────────────┐
                  │     Dim_Date     │
                  └──────────────────┘
                           │
                           │ 1
                           │ *
                  ┌────────┴─────────┐
                  │ Fact_Returns_    │
                  │ Refunds          │
                  └──────────────────┘
                           │ *
                           │ *
                  ┌────────┴─────────┐
                  │ Bridge_Identity  │
                  │ Network          │
                  └──────────────────┘
```

### Table Relationships & Cardinality:
| From Table | From Column | To Table | To Column | Cardinality | Cross Filter |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Dim_Customer` | `customer_id` | `Fact_Orders` | `customer_id` | 1 to Many (*) | Single |
| `Dim_Merchant` | `merchant_id` | `Fact_Orders` | `merchant_id` | 1 to Many (*) | Single |
| `Dim_DeliveryPartner` | `delivery_partner_id` | `Fact_Orders` | `delivery_partner_id` | 1 to Many (*) | Single |
| `Dim_Date` | `Date` | `Fact_Orders` | `order_date` | 1 to Many (*) | Single |
| `Fact_Orders` | `order_id` | `Fact_Returns_Refunds` | `order_id` | 1 to Many (*) | Both |
| `Dim_Customer` | `customer_id` | `Bridge_IdentityNetwork` | `customer_id` | 1 to Many (*) | Both |

---

## 2. Palette & Design Guidelines

- **Background**: `#0F172A` (Deep Slate Navy)
- **Card Background**: `#1E293B` (Soft Slate) with 1px border `#334155`
- **Low Risk / Approved**: `#10B981` (Emerald Green)
- **Medium Risk / Manual Review**: `#F59E0B` (Amber Gold)
- **High Risk / Investigate**: `#EF4444` (Crimson Red)
- **Primary Accent**: `#3B82F6` (Electric Blue)
- **Typography**: Segoe UI / Inter, bold KPI numbers (28–36pt)

---

## 3. Page Layouts & Visual Wireframes

### Page 1: Executive Overview (C-Suite & Risk Leadership)
- **Top KPI Strip (5 Cards)**:
  1. `Total Orders`: Total count and total revenue volume.
  2. `Total Returns & Return Rate %`: e.g. 55.8% return rate.
  3. `Fraud Loss Prevented`: Total INR amount intercepted at manual review.
  4. `Fraud Recovery Rate %`: % of flagged refunds withheld.
  5. `High-Risk Orders Count`: Highlighted in red.
- **Visuals**:
  - **Left Area (Donut Chart)**: Risk Level Distribution (Low Risk vs Medium Risk vs High Risk).
  - **Center Area (Area / Line Chart)**: Order Volume vs Refund Amount trend over time (using `Dim_Date[Month]`).
  - **Right Area (Clustered Bar Chart)**: Financial Loss by Category (Fashion vs Electronics vs Home).
- **Global Slicers**: Date Range, Category, City, Risk Level.

---

### Page 2: Customer Risk Profiler
- **Summary KPIs**:
  - `High Risk Customers Count`
  - `Serial Returners Count` (Customers with >65% return rate and >=3 orders)
  - `Average Accounts per Device`
- **Visuals**:
  - **Scatter Plot**: X-axis: `Total Orders`, Y-axis: `Return Rate %`, Bubble Size: `Total Spend`, Color: `Risk Level`.
  - **Customer Deep Dive Table**:
    `Customer ID` | `City` | `Account Age` | `Total Orders` | `Returns` | `Return Rate %` | `Avg Risk Score` | `Action`
  - **Detail Card**: Shows itemized rules triggered for selected customer.

---

### Page 3: Fraud Typology Breakdown
- **Visuals**:
  - **Treemap / Horizontal Bar Chart**: Total loss volume by `fraud_type` (Wardrobing, Empty Box, Item Switching, Serial Returning, Bracketing, Fake INR, Chargeback Fraud).
  - **Table**: Fraud Typology vs Detected Cases vs Average Order Value vs Recovery Rate %.
  - **Physical Inspection Matrix**: Weight Loss % distribution for Empty Box and Item Switching returns.

---

### Page 4: Merchant & Delivery Partner Risk
- **Visuals**:
  - **Delivery Partner Risk Matrix (Scatter Plot)**: X-axis: `Total Deliveries`, Y-axis: `Tampering Cases`, Color: `partner_risk_score`.
  - **Merchant Refund Leakage Table**: `Merchant ID` | `Category` | `Total Orders` | `Return Rate %` | `Fraud Rate %` | `Risk Tier`.
  - **Anomaly Alert Card**: Highlighting couriers or merchants with abnormal variance.

---

### Page 5: Network & Identity Syndicate Explorer
- **Visuals**:
  - **Multi-Account Matrix**: Devices linked to >= 2 distinct customer accounts.
  - **Shared Phone & Address Clusters**: Listing linked customer accounts sharing hardware or shipping locations.
  - **Cross-Account Dispute Impact**: Cumulative fraud losses associated with each device cluster.

---

## 4. How to Import in Power BI Desktop (Step-by-Step)

1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Navigate to `power_bi/data/` and import all 7 CSV files:
   - `Dim_Customer.csv`
   - `Dim_Merchant.csv`
   - `Dim_DeliveryPartner.csv`
   - `Dim_Date.csv`
   - `Fact_Orders.csv`
   - `Fact_Returns_Refunds.csv`
   - `Bridge_IdentityNetwork.csv`
4. In the **Model View**, verify the relationships listed in Section 1. Set cross-filtering directions as indicated.
5. Create a new measure table: Click **Enter Data**, name it `_Measures`.
6. Open [`power_bi/measures.dax`](file:///c:/Users/asus/Downloads/RefundShield_Dataset/power_bi/measures.dax) in a text editor, copy each formula, and click **New Measure** in Power BI.
7. Build the visual pages according to the wireframes described in Section 3.
