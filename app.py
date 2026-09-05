"""
RefundShield AI - Interactive E-Commerce Refund & Return Fraud Detection System
Live Command Center, Executive Analytics, Identity Graph Explorer, and Real-Time Fraud Sandbox.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Internal modules
from src.data.data_loader import load_raw_tables, get_merged_master_data
from src.scoring.hybrid_engine import HybridFraudEngine
from src.graph.network_analyzer import IdentityNetworkAnalyzer

st.set_page_config(
    page_title="RefundShield AI - Fraud Detection Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Glassmorphic Theme
st.markdown("""
<style>
    /* Global Styling */
    .stApp {
        background-color: #0B1120;
        color: #F1F5F9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    /* Metric Cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.85rem;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 0.82rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .delta-green { color: #10B981; }
    .delta-red { color: #EF4444; }
    .delta-amber { color: #F59E0B; }
    
    /* Risk Badges */
    .badge-high {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-medium {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-low {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    
    /* Table Styling */
    div[data-testid="stDataFrame"] {
        background-color: #1E293B;
        border-radius: 8px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_hybrid_engine():
    return HybridFraudEngine()


@st.cache_resource
def get_network_analyzer():
    return IdentityNetworkAnalyzer()


@st.cache_data
def get_data():
    tables = load_raw_tables()
    master_df = get_merged_master_data(tables)
    eval_df = tables.get("fraud_training_data", pd.DataFrame())
    return tables, master_df, eval_df


tables, master_df, eval_df = get_data()
engine = get_hybrid_engine()
network_analyzer = get_network_analyzer()

# Header Banner
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="margin: 0; color: #38BDF8; font-size: 2.2rem; font-weight: 800;">
                🛡️ RefundShield AI
            </h1>
            <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 1.05rem;">
                AI-Powered E-Commerce Refund & Return Fraud Detection Platform
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: #0F172A; border: 1px solid #0284C7; color: #38BDF8; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">
                Engine v2.4 • Multi-Layer Hybrid
            </span>
            <div style="color: #64748B; font-size: 0.8rem; margin-top: 4px;">
                Status: Production Online
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tabs = st.tabs([
    "📊 Executive Command Center",
    "👤 Customer Risk Profiler",
    "🕸️ Identity Network & Rings",
    "🏷️ Fraud Typology Deep-Dive",
    "🚚 Merchant & Courier Risk",
    "⚡ Live Fraud Sandbox"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE COMMAND CENTER
# -----------------------------------------------------------------------------
with tabs[0]:
    total_orders = len(master_df)
    return_col = "return_id" if "return_id" in master_df.columns else ("return_id_x" if "return_id_x" in master_df.columns else None)
    total_returns = master_df[return_col].dropna().nunique() if return_col else len(tables.get("returns", []))
    ret_rate = (total_returns / max(1, total_orders)) * 100.0
    total_spend = master_df["order_amount"].sum()
    total_refunds = master_df["refund_amount"].sum() if "refund_amount" in master_df.columns else 0.0
    
    # Fraud loss prevented
    flagged_orders = eval_df[eval_df["risk_score"] >= 71] if not eval_df.empty else pd.DataFrame()
    fraud_loss_intercepted = flagged_orders["order_amount"].sum() if not flagged_orders.empty else 0.0
    high_risk_count = len(flagged_orders)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Orders Evaluated</div>
            <div class="metric-value">{total_orders:,}</div>
            <div class="metric-delta delta-green">Rs. {total_spend:,.0f} Volume</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Returns Requested</div>
            <div class="metric-value">{total_returns:,}</div>
            <div class="metric-delta delta-amber">{ret_rate:.1f}% Return Rate</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Refund Payouts</div>
            <div class="metric-value">Rs. {total_refunds:,.0f}</div>
            <div class="metric-delta delta-amber">{((total_refunds/max(1, total_spend))*100):.1f}% Revenue Leakage</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Loss Prevented (High Risk)</div>
            <div class="metric-value" style="color: #10B981;">Rs. {fraud_loss_intercepted:,.0f}</div>
            <div class="metric-delta delta-green">Intercepted at Gate</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">High Risk Incidents</div>
            <div class="metric-value" style="color: #EF4444;">{high_risk_count:,}</div>
            <div class="metric-delta delta-red">{((high_risk_count/max(1, total_orders))*100):.1f}% Incident Rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns([1, 2])
    with col_chart1:
        st.subheader("Risk Tier Distribution")
        if not eval_df.empty:
            tier_counts = eval_df["risk_level"].value_counts().reset_index()
            tier_counts.columns = ["Risk Tier", "Count"]
            color_map = {"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"}
            fig_pie = px.pie(
                tier_counts,
                names="Risk Tier",
                values="Count",
                hole=0.55,
                color="Risk Tier",
                color_discrete_map=color_map
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F1F5F9"),
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Financial Volume by Product Category")
        cat_agg_dict = {"order_amount": "sum"}
        if return_col and return_col in master_df.columns:
            cat_agg_dict[return_col] = "count"
        cat_df = master_df.groupby("category").agg(cat_agg_dict).reset_index()
        if return_col and return_col in cat_df.columns:
            cat_df = cat_df.rename(columns={return_col: "return_count"})
        else:
            cat_df["return_count"] = 0
        
        fig_bar = px.bar(
            cat_df,
            x="category",
            y="order_amount",
            color="return_count",
            color_continuous_scale="Viridis",
            labels={"order_amount": "Gross Sales (Rs.)", "return_count": "Returns Count", "category": "Category"},
            text_auto=".2s"
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F1F5F9"),
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(gridcolor="#334155"),
            yaxis=dict(gridcolor="#334155")
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 2: CUSTOMER RISK PROFILER
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Customer Investigation & Risk Profiling")
    
    all_cust_ids = sorted(tables["customers"]["customer_id"].unique())
    selected_cid = st.selectbox("Select Customer ID for Deep Dive:", all_cust_ids, index=0)
    
    c_info = tables["customers"][tables["customers"]["customer_id"] == selected_cid].iloc[0]
    c_orders = master_df[master_df["customer_id"] == selected_cid]
    c_links = tables["identity_links"][tables["identity_links"]["customer_id"] == selected_cid]
    
    net_risk = network_analyzer.evaluate_customer_network_risk(selected_cid)
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        st.markdown(f"**Customer ID:** `{selected_cid}`")
        st.markdown(f"**Account Age:** `{c_info['account_age_days']} days`")
        st.markdown(f"**Registration:** `{c_info['registration_date']}`")
    with col_c2:
        st.markdown(f"**City:** `{c_info['city']}`")
        st.markdown(f"**Account Status:** `{c_info['account_status']}`")
        st.markdown(f"**Prior Fraud Flag:** `{'YES' if c_info['previous_fraud_flag'] == 1 else 'NO'}`")
    with col_c3:
        st.markdown(f"**Total Orders:** `{len(c_orders)}`")
        if return_col and return_col in c_orders.columns:
            total_c_ret = c_orders[return_col].dropna().nunique()
        else:
            total_c_ret = len(tables.get("returns", pd.DataFrame()).query(f"customer_id == '{selected_cid}'")) if not tables.get("returns", pd.DataFrame()).empty else 0
        st.markdown(f"**Total Returns:** `{total_c_ret}`")
        ret_rate_c = (total_c_ret / max(1, len(c_orders))) * 100.0
        st.markdown(f"**Return Rate:** `{ret_rate_c:.1f}%`")
    with col_c4:
        st.markdown(f"**Network Ring Size:** `{net_risk['ring_size']} account(s)`")
        st.markdown(f"**Sybil Ring Member:** `{'YES' if net_risk['is_in_sybil_ring'] else 'NO'}`")
        st.markdown(f"**Flagged Neighbors:** `{net_risk['flagged_connected_accounts']}`")

    st.markdown("---")
    st.subheader(f"Transaction History for {selected_cid}")
    if not c_orders.empty:
        display_cols = [
            "order_id", "order_date", "category", "order_amount", "delivery_status",
            "return_reason", "returned_weight_kg", "product_condition", "refund_status"
        ]
        available_cols = [c for c in display_cols if c in c_orders.columns]
        st.dataframe(c_orders[available_cols], use_container_width=True)
    else:
        st.info("No recorded transactions found for this customer.")


# -----------------------------------------------------------------------------
# TAB 3: IDENTITY NETWORK & FRAUD RINGS
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Identity Graph Syndicate Explorer")
    st.markdown("""
    Graph network mapping **Customer → Hardware Device → Phone Hash → Shipping Address → Payment Fingerprint**.
    Identifies organized fraud rings, Sybil attacks, and multi-account return abusers.
    """)

    rings = network_analyzer.find_fraud_rings(min_accounts=2)
    
    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        st.markdown(f"### Detected Multi-Account Rings ({len(rings)})")
        for r in rings[:6]:
            with st.expander(f"🔴 {r['ring_id']} ({r['account_count']} Accounts, {r['flagged_accounts_count']} Flagged)"):
                st.write("**Member Customers:**", ", ".join(r["customers"][:8]))
                st.write("**Shared Devices:**", ", ".join(r["shared_devices"][:4]))
                st.write("**Shared Addresses:**", ", ".join(r["shared_addresses"][:4]))
                st.write("**Ring Risk Level:**", r["ring_risk_level"])

    with col_r2:
        st.markdown("### Interactive Entity Graph")
        graph_data = network_analyzer.get_plotly_graph_elements(max_nodes=100)
        
        edge_trace = go.Scatter(
            x=graph_data["edge_x"], y=graph_data["edge_y"],
            line=dict(width=1, color="#475569"),
            hoverinfo="none",
            mode="lines"
        )
        node_trace = go.Scatter(
            x=graph_data["node_x"], y=graph_data["node_y"],
            mode="markers",
            hoverinfo="text",
            text=graph_data["node_text"],
            marker=dict(
                color=graph_data["node_color"],
                size=graph_data["node_size"],
                line_width=1.5,
                line_color="#0F172A"
            )
        )
        fig_graph = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                showlegend=False,
                hovermode="closest",
                margin=dict(b=10, l=10, r=10, t=10),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
        )
        st.plotly_chart(fig_graph, use_container_width=True)
        st.caption("🔵 Blue: Genuine Customer | 🔴 Red: Flagged Fraud Customer | 🟣 Purple: Device | 🟢 Green: Phone | 🟠 Orange: Address")


# -----------------------------------------------------------------------------
# TAB 4: FRAUD TYPOLOGY DEEP-DIVE
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Fraud Typology Taxonomy & Analysis")
    st.markdown("Distribution and financial exposure across all 12+ industry return fraud schemes.")

    if not eval_df.empty:
        type_agg = eval_df.groupby("fraud_type").agg({
            "order_id": "count",
            "order_amount": "sum",
            "risk_score": "mean"
        }).reset_index()
        type_agg.columns = ["Fraud Typology", "Incident Count", "Total Exposure (Rs.)", "Avg Risk Score"]
        type_agg = type_agg.sort_values(by="Total Exposure (Rs.)", ascending=False)

        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            fig_types = px.bar(
                type_agg[type_agg["Fraud Typology"] != "Legitimate"],
                x="Total Exposure (Rs.)",
                y="Fraud Typology",
                orientation="h",
                color="Avg Risk Score",
                color_continuous_scale="Reds",
                text_auto=".2s",
                title="Fraud Typology by Financial Exposure"
            )
            fig_types.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F1F5F9"),
                yaxis=dict(categoryorder="total ascending", gridcolor="#334155"),
                xaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_types, use_container_width=True)

        with col_t2:
            st.dataframe(type_agg, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 5: MERCHANT & COURIER RISK
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Supply Chain Risk: Delivery Partners & Merchants")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("### Delivery Partner Tampering Rates")
        dp_df = tables.get("delivery_partners", pd.DataFrame())
        if not dp_df.empty:
            fig_dp = px.scatter(
                dp_df,
                x="total_deliveries",
                y="tampering_cases",
                size="partner_risk_score",
                color="partner_risk_score",
                color_continuous_scale="Reds",
                hover_name="delivery_partner_id",
                text="delivery_partner_id",
                title="Carrier Deliveries vs Tampering Incidents"
            )
            fig_dp.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F1F5F9"),
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_dp, use_container_width=True)

    with col_m2:
        st.markdown("### Merchant Refund Leakage")
        m_df = tables.get("merchants", pd.DataFrame())
        if not m_df.empty:
            fig_m = px.bar(
                m_df,
                x="merchant_id",
                y="return_rate",
                color="merchant_risk_score",
                color_continuous_scale="Oranges",
                title="Merchant Return Rates & Risk Index"
            )
            fig_m.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F1F5F9"),
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_m, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 6: LIVE FRAUD SANDBOX (INTERACTIVE SIMULATOR)
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Interactive Real-Time Fraud Simulator")
    st.markdown("Adjust customer behavior, identity velocity, and package inspection signals to test the live hybrid engine.")

    with st.form("sandbox_form"):
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            st.markdown("#### 🛍️ Order & Product Profile")
            sb_amount = st.number_input("Order Amount (Rs.)", min_value=100.0, max_value=100000.0, value=22500.0, step=500.0)
            sb_cat = st.selectbox("Product Category", ["Electronics", "Fashion", "Beauty", "Footwear", "Home", "Grocery"], index=0)
            sb_orders = st.slider("Customer Total Orders", min_value=1, max_value=30, value=6)
            sb_returns = st.slider("Customer Total Returns", min_value=0, max_value=30, value=5)
            sb_prev_fraud = st.selectbox("Prior Confirmed Fraud Flag?", [0, 1], index=1)

        with col_s2:
            st.markdown("#### 📦 Physical Return & Package Inspection")
            sb_orig_wt = st.number_input("Original Delivered Weight (kg)", min_value=0.1, max_value=25.0, value=3.2, step=0.1)
            sb_ret_wt = st.number_input("Returned Package Weight (kg)", min_value=0.0, max_value=25.0, value=0.4, step=0.1)
            sb_item_match = st.selectbox("Barcode/Item Match Verified?", [1.0, 0.0], index=1, help="0.0 indicates returned item SKU mismatch")
            sb_condition = st.selectbox("Product Condition", ["Good", "Used", "Missing", "Defective"], index=0)
            sb_reason = st.selectbox("Return Reason Stated", ["Wrong Item", "Changed mind", "Size issue", "Item not received", "Defective product"], index=0)

        with col_s3:
            st.markdown("#### 📱 Identity Velocity & Third Party")
            sb_addr = st.slider("Address Changes Count", min_value=0, max_value=6, value=3)
            sb_phone = st.slider("Phone Hash Changes Count", min_value=0, max_value=5, value=2)
            sb_devices = st.slider("Accounts Linked to this Device", min_value=1, max_value=8, value=4)
            sb_cb = st.selectbox("Bank Chargeback Disputed?", [0, 1], index=0)
            sb_dp_risk = st.slider("Courier Partner Risk Score", min_value=5, max_value=90, value=35)

        evaluate_btn = st.form_submit_button("⚡ Evaluate Transaction in Real-Time", use_container_width=True)

    if evaluate_btn:
        sim_input = {
            "order_id": "SIM_ORD_001",
            "customer_id": "C0005",
            "order_amount": sb_amount,
            "category": sb_cat,
            "customer_order_count": sb_orders,
            "customer_return_count": sb_returns,
            "return_rate": (sb_returns / max(1, sb_orders)) * 100.0,
            "original_weight_kg": sb_orig_wt,
            "returned_weight_kg": sb_ret_wt,
            "item_match_flag": sb_item_match,
            "product_condition": sb_condition,
            "return_reason": sb_reason,
            "address_changes": sb_addr,
            "phone_changes": sb_phone,
            "device_account_count": sb_devices,
            "previous_fraud": sb_prev_fraud,
            "chargeback_count": sb_cb,
            "delivery_partner_risk": sb_dp_risk
        }

        eval_res = engine.evaluate_transaction(sim_input, persist_audit=True)

        st.markdown("---")
        st.subheader("Evaluation Decision & Audit Breakdown")

        r_col1, r_col2, r_col3 = st.columns([1, 1, 2])
        with r_col1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=eval_res["hybrid_risk_score"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Fraud Risk Score", 'font': {'size': 20, 'color': '#F1F5F9'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#F1F5F9"},
                    'bar': {'color': eval_res["badge_color"]},
                    'bgcolor': "#1E293B",
                    'borderwidth': 2,
                    'bordercolor': "#334155",
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.2)'},
                        {'range': [30, 70], 'color': 'rgba(245, 158, 11, 0.2)'},
                        {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.2)'}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#F1F5F9"), height=260)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with r_col2:
            st.markdown(f"### Classification:")
            if eval_res["risk_level"] == "High Risk":
                st.markdown('<span class="badge-high">HIGH RISK (71-100)</span>', unsafe_allow_html=True)
            elif eval_res["risk_level"] == "Medium Risk":
                st.markdown('<span class="badge-medium">MEDIUM RISK (31-70)</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge-low">LOW RISK (0-30)</span>', unsafe_allow_html=True)

            st.markdown(f"**Recommended Action:**")
            st.markdown(f"### `{eval_res['recommended_action']}`")
            st.markdown(f"**Probable Fraud Type:** `{eval_res['probable_fraud_type']}` (Confidence: {eval_res['typology_confidence']*100:.0f}%)")

            st.markdown("---")
            st.write(f"• **Rule-Based Engine Score:** `{eval_res['rule_score']}/100`")
            st.write(f"• **ML Model Probability:** `{eval_res['ml_probability']:.2f}`")
            st.write(f"• **Network Graph Risk Penalty:** `+{eval_res['network_risk_points']} pts`")

        with r_col3:
            st.markdown("### Itemized Audit Reasons (Explainability):")
            for idx, rsn in enumerate(eval_res["reasons"]):
                st.markdown(f"**{idx + 1}.** {rsn}")
