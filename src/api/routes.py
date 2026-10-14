"""
RefundShield AI - FastAPI Dynamic Asynchronous API Routes
Provides production-grade endpoints for Customer 360 Dossiers, Orders, Live Real-Time Evaluations, Search, and Analytics.
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    CustomerLookupResponse,
    OrderDetailsResponse,
    TransactionEvaluationRequest,
    FraudRiskEvaluation,
    TriggeredRule,
    KPIResponse,
    SearchResultItem,
    ErrorResponse
)
from src.services.customer_service import get_customer_dossier, list_customers_summary
from src.services.order_service import get_order_details
from src.services.search_service import global_search
from src.services.analytics_service import (
    get_executive_kpis,
    get_risk_distribution,
    get_fraud_typologies,
    get_supply_chain_risks
)

api_router = APIRouter(prefix="/api", tags=["RefundShield AI Core Endpoints"])


@api_router.get(
    "/health",
    tags=["System"],
    summary="System Health & Model Telemetry",
    response_model=Dict[str, Any]
)
async def health_check(request: Request):
    """
    Returns engine uptime, active model types, and identity graph topology nodes.
    """
    engine = getattr(request.app.state, "hybrid_engine", None)
    network_analyzer = getattr(request.app.state, "network_analyzer", None)
    return {
        "status": "healthy",
        "service": "RefundShield AI Enterprise Engine",
        "model_type": engine.model_type if engine else "Rule Fallback",
        "typology_model": "Active" if engine and getattr(engine, "typology_predictor", None) else "Offline",
        "graph_nodes": network_analyzer.graph.number_of_nodes() if network_analyzer else 0,
        "graph_edges": network_analyzer.graph.number_of_edges() if network_analyzer else 0,
        "version": "2.4.0-cloud"
    }


@api_router.get(
    "/search",
    response_model=List[SearchResultItem],
    summary="Global Autocomplete Search Across Entities"
)
async def search_entities(
    q: str = Query(..., min_length=1, max_length=100, description="Customer ID, Order ID, Device ID, or City")
):
    """
    Sub-millisecond multi-entity lookup returning typed suggestions with risk hints.
    """
    return global_search(query=q, limit=12)


@api_router.get(
    "/customers",
    summary="Paginated Customer Directory"
)
async def get_customers(
    page: int = Query(1, ge=1, description="Page index"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    search: str = Query("", max_length=100, description="Filter by customer ID or city"),
    risk: str = Query("", description="Filter by risk tier: Low, Medium, High")
):
    """
    Retrieves paginated customer summaries with aggregate return rates and risk classifications.
    """
    return list_customers_summary(page=page, limit=limit, search=search, risk_filter=risk)


@api_router.get(
    "/customers/{customer_id}",
    response_model=CustomerLookupResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Customer not found"}
    },
    summary="Customer 360 Dossier & Multi-Layer Fraud Scoring"
)
async def get_customer(
    customer_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Dynamically compiles:
    - Customer demographic profile & account status
    - Complete historical orders ledger (with physical delivery, return telemetry, and refund payouts)
    - Identity & hardware device syndicate footprint
    - Real-time Hybrid Risk Score (0-100), Risk Tier, Recommended Action, Typology, and Itemized Explainability.
    """
    cid = customer_id.strip().upper()
    engine = getattr(request.app.state, "hybrid_engine", None)
    network_analyzer = getattr(request.app.state, "network_analyzer", None)

    dossier = get_customer_dossier(
        customer_id=cid,
        hybrid_engine=engine,
        network_analyzer=network_analyzer,
        db=db
    )
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "CUSTOMER_NOT_FOUND",
                "message": f"Customer ID '{cid}' does not exist in the database.",
                "suggested_ids": ["C0022", "C0061", "C0020", "C0001", "C0005"]
            }
        )
    return dossier


@api_router.get(
    "/orders/{order_id}",
    response_model=OrderDetailsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Order not found"}
    },
    summary="Order Risk Inspection & Package Telemetry"
)
async def get_order(
    order_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete relational telemetry for a specific order:
    joined fulfillment metrics, delivery partner tampering history, merchant return rate,
    package weight deficit percentage, SKU match verification, and live fraud scoring.
    """
    oid = order_id.strip().upper()
    engine = getattr(request.app.state, "hybrid_engine", None)
    network_analyzer = getattr(request.app.state, "network_analyzer", None)

    order_data = get_order_details(
        order_id=oid,
        hybrid_engine=engine,
        network_analyzer=network_analyzer,
        db=db
    )
    if not order_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ORDER_NOT_FOUND",
                "message": f"Order ID '{oid}' does not exist in the database.",
                "suggested_ids": ["O00231", "O00045", "O00120"]
            }
        )
    return order_data


@api_router.post(
    "/evaluate",
    response_model=FraudRiskEvaluation,
    summary="Real-Time Flexible Transaction & Return Evaluator"
)
async def evaluate_transaction(
    payload: TransactionEvaluationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Executes real-time multi-layer fraud scoring on an incoming transaction or return request.
    If 'customer_id' is provided, it intelligently auto-populates historical customer baselines
    (lifetime orders, returns, device sharing, prior fraud) from the relational database.
    """
    engine = getattr(request.app.state, "hybrid_engine", None)
    network_analyzer = getattr(request.app.state, "network_analyzer", None)

    cid = str(payload.customer_id).strip().upper() if payload.customer_id else "ANONYMOUS"
    oid = str(payload.order_id).strip().upper() if payload.order_id else "LIVE_EVAL"

    c_orders = payload.customer_order_count
    c_returns = payload.customer_return_count
    ret_rate = payload.return_rate
    prev_fraud = payload.previous_fraud
    cb_count = payload.chargeback_count
    dev_accounts = payload.device_account_count
    addr_changes = payload.address_changes or 0
    phone_changes = payload.phone_changes or 0

    # Auto-enrich from customer database if customer_id exists
    if payload.customer_id and (c_orders is None or ret_rate is None or prev_fraud is None):
        dossier = get_customer_dossier(
            customer_id=cid,
            hybrid_engine=engine,
            network_analyzer=network_analyzer,
            db=db
        )
        if dossier:
            if c_orders is None:
                c_orders = dossier.metrics.total_orders
            if c_returns is None:
                c_returns = dossier.metrics.total_returns
            if ret_rate is None:
                ret_rate = dossier.metrics.return_rate
            if prev_fraud is None:
                prev_fraud = dossier.customer.previous_fraud_flag
            if cb_count is None:
                cb_count = dossier.metrics.chargebacks_count
            if dev_accounts is None:
                dev_accounts = max([d.account_count for d in dossier.identity.devices] or [1])
            if payload.address_changes is None:
                addr_changes = max(0, len(dossier.identity.addresses) - 1)
            if payload.phone_changes is None:
                phone_changes = max(0, len(dossier.identity.phones) - 1)

    c_orders = c_orders if c_orders is not None else 1
    c_returns = c_returns if c_returns is not None else 0
    ret_rate = ret_rate if ret_rate is not None else round((c_returns / max(1, c_orders)) * 100.0, 1)
    prev_fraud = prev_fraud if prev_fraud is not None else 0
    cb_count = cb_count if cb_count is not None else 0
    dev_accounts = dev_accounts if dev_accounts is not None else 1

    orig_wt = float(payload.original_weight_kg) if payload.original_weight_kg is not None else 1.5
    ret_wt = float(payload.returned_weight_kg) if payload.returned_weight_kg is not None else orig_wt
    wt_loss = max(0.0, round(((orig_wt - ret_wt) / max(0.01, orig_wt)) * 100.0, 1))

    eval_dict = {
        "order_id": oid,
        "customer_id": cid,
        "order_amount": float(payload.order_amount or 1500.0),
        "category": str(payload.category or "Electronics"),
        "customer_order_count": c_orders,
        "customer_return_count": c_returns,
        "return_rate": ret_rate,
        "original_weight_kg": orig_wt,
        "returned_weight_kg": ret_wt,
        "weight_difference_pct": wt_loss,
        "item_match_flag": float(payload.item_match_flag if payload.item_match_flag is not None else 1.0),
        "product_condition": str(payload.product_condition or "Good"),
        "return_reason": str(payload.return_reason or "Changed mind"),
        "address_changes": addr_changes,
        "phone_changes": phone_changes,
        "device_account_count": dev_accounts,
        "previous_fraud": prev_fraud,
        "chargeback_count": cb_count,
        "delivery_partner_risk": float(payload.delivery_partner_risk or 20.0),
        "package_tampered": int(payload.package_tampered or 0)
    }

    eval_res = engine.evaluate_transaction(eval_dict, persist_audit=True)

    return FraudRiskEvaluation(
        order_id=oid,
        customer_id=cid,
        hybrid_risk_score=eval_res["hybrid_risk_score"],
        risk_level=eval_res["risk_level"],
        recommended_action=eval_res["recommended_action"],
        badge_color=eval_res["badge_color"],
        probable_fraud_type=eval_res["probable_fraud_type"],
        typology_confidence=round(eval_res["typology_confidence"], 3),
        rule_score=eval_res["rule_score"],
        ml_probability=round(eval_res["ml_probability"], 3),
        network_risk_points=eval_res["network_risk_points"],
        ring_size=eval_res["ring_size"],
        reasons=eval_res["reasons"],
        triggered_rules=[
            TriggeredRule(
                rule_id=r["rule_id"],
                points=r["points"],
                description=r["description"]
            ) for r in eval_res.get("triggered_rules", [])
        ]
    )


@api_router.get(
    "/analytics/kpis",
    response_model=KPIResponse,
    summary="Executive Command Center Enterprise KPIs"
)
async def get_kpis(request: Request):
    """
    Returns real-time macro analytics across entire customer base and transaction volume.
    """
    network_analyzer = getattr(request.app.state, "network_analyzer", None)
    return get_executive_kpis(network_analyzer=network_analyzer)


@api_router.get(
    "/analytics/risk-distribution",
    summary="Risk Tier Distribution"
)
async def get_tiers():
    """
    Returns counts and proportions for Low, Medium, and High risk tiers.
    """
    return get_risk_distribution()


@api_router.get(
    "/analytics/fraud-typologies",
    summary="Fraud Typology Financial Exposure Breakdown"
)
async def get_typologies():
    """
    Returns fraud typology categories, financial exposure, and mean risk scores.
    """
    return get_fraud_typologies()


@api_router.get(
    "/analytics/fraud-rings",
    summary="Sybil & Fraud Rings Detection"
)
async def get_rings(request: Request):
    """
    Returns detected multi-account fraud syndicates and member customer accounts.
    """
    network_analyzer = getattr(request.app.state, "network_analyzer", None)
    rings = network_analyzer.find_fraud_rings(min_accounts=2) if network_analyzer else []
    return {
        "total_rings": len(rings),
        "rings": rings
    }


@api_router.get(
    "/analytics/supply-chain",
    summary="Merchant & Courier Supply Chain Risks"
)
async def get_supply_chain():
    """
    Returns carrier tampering incident logs and merchant return leakage metrics.
    """
    return get_supply_chain_risks()
