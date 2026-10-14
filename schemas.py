"""
RefundShield AI - Strict Pydantic v2 Schemas & Data Validation
Ensures type safety, strict boundary constraints, and structured error responses.
"""

from typing import List, Dict, Any, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1. Base Entity Schemas
# ============================================================================

class CustomerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(..., description="Unique Customer Identifier (e.g. C0022)", min_length=2, max_length=50)
    account_age_days: int = Field(..., ge=0, description="Account age in days")
    registration_date: date
    gender: Optional[str] = Field(default="N/A", max_length=10)
    city: str = Field(..., min_length=2, max_length=100)
    previous_fraud_flag: int = Field(default=0, ge=0, le=1, description="1 if prior fraud confirmed")
    account_status: str = Field(default="Active", max_length=50)


class CustomerMetrics(BaseModel):
    total_orders: int = Field(..., ge=0)
    total_spend: float = Field(..., ge=0.0)
    avg_order_value: float = Field(..., ge=0.0)
    total_returns: int = Field(..., ge=0)
    return_rate: float = Field(..., ge=0.0, le=100.0)
    total_refunds: float = Field(..., ge=0.0)
    refund_leakage_pct: float = Field(..., ge=0.0)
    chargebacks_count: int = Field(default=0, ge=0)
    suspicious_returns_count: int = Field(default=0, ge=0)
    categories_bought: List[str] = []
    top_return_reasons: List[str] = []


class DeviceLink(BaseModel):
    device_id: str
    account_count: int = Field(default=1, ge=1)


class IdentityFootprint(BaseModel):
    devices: List[DeviceLink] = []
    addresses: List[str] = []
    phones: List[str] = []
    payment_fingerprints: List[str] = []
    is_in_sybil_ring: bool = False
    ring_id: Optional[str] = None
    ring_size: int = Field(default=1, ge=1)
    flagged_neighbors_count: int = Field(default=0, ge=0)
    syndicate_risk_penalty: float = Field(default=0.0, ge=0.0, le=30.0)
    network_summary: str = "Clean network profile"


class OrderLedgerItem(BaseModel):
    order_id: str
    order_date: str
    category: str
    order_amount: float = Field(..., ge=0.0)
    delivery_status: str = "Delivered"
    courier_id: Optional[str] = None
    original_weight_kg: Optional[float] = None
    returned_weight_kg: Optional[float] = None
    weight_loss_pct: Optional[float] = None
    return_reason: Optional[str] = None
    product_condition: Optional[str] = None
    item_match_flag: Optional[float] = 1.0
    refund_amount: Optional[float] = None
    refund_status: Optional[str] = None
    payment_method: Optional[str] = None
    chargeback_flag: int = 0


class TriggeredRule(BaseModel):
    rule_id: str
    points: int
    description: str


class FraudRiskEvaluation(BaseModel):
    order_id: Optional[str] = None
    customer_id: str
    hybrid_risk_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="Low Risk, Medium Risk, or High Risk")
    recommended_action: str = Field(..., description="Approve, Manual Review, or Investigate / Block")
    badge_color: str
    probable_fraud_type: str
    typology_confidence: float = Field(..., ge=0.0, le=1.0)
    rule_score: float = Field(..., ge=0.0, le=100.0)
    ml_probability: float = Field(..., ge=0.0, le=1.0)
    network_risk_points: float = Field(..., ge=0.0, le=30.0)
    ring_size: int = Field(default=1, ge=1)
    reasons: List[str] = []
    triggered_rules: List[TriggeredRule] = []


# ============================================================================
# 2. Main Response Schemas
# ============================================================================

class CustomerLookupResponse(BaseModel):
    """Single comprehensive response aggregating Customer Profile, Metrics, Identity Graph, and Orders."""
    customer: CustomerBase
    metrics: CustomerMetrics
    identity: IdentityFootprint
    risk_evaluation: FraudRiskEvaluation
    orders: List[OrderLedgerItem] = []


class OrderDetailsResponse(BaseModel):
    order_id: str
    customer_id: str
    merchant_id: str
    product_id: str
    category: str
    order_amount: float
    order_date: str
    delivery: Dict[str, Any] = {}
    return_info: Optional[Dict[str, Any]] = None
    refund_info: Optional[Dict[str, Any]] = None
    payment: Optional[Dict[str, Any]] = None
    customer_summary: Optional[Dict[str, Any]] = None
    risk_evaluation: FraudRiskEvaluation


# ============================================================================
# 3. Dynamic Evaluation & Transaction Request Schemas
# ============================================================================

class TransactionEvaluationRequest(BaseModel):
    """
    Flexible transaction evaluation payload.
    If 'customer_id' is supplied, historical baselines (return rate, prior fraud, device sharing)
    are automatically enriched from the database if not explicitly provided.
    """
    order_id: Optional[str] = Field(default=None, max_length=50)
    customer_id: Optional[str] = Field(default=None, max_length=50)
    order_amount: Optional[float] = Field(default=1500.0, ge=1.0, le=1000000.0)
    category: Optional[str] = Field(default="Electronics", max_length=100)
    customer_order_count: Optional[int] = Field(default=None, ge=1, le=500)
    customer_return_count: Optional[int] = Field(default=None, ge=0, le=500)
    return_rate: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    original_weight_kg: Optional[float] = Field(default=1.5, ge=0.01, le=100.0)
    returned_weight_kg: Optional[float] = Field(default=1.5, ge=0.0, le=100.0)
    item_match_flag: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    product_condition: Optional[str] = Field(default="Good", max_length=50)
    return_reason: Optional[str] = Field(default="Changed mind", max_length=100)
    address_changes: Optional[int] = Field(default=None, ge=0, le=50)
    phone_changes: Optional[int] = Field(default=None, ge=0, le=50)
    device_account_count: Optional[int] = Field(default=None, ge=1, le=50)
    previous_fraud: Optional[int] = Field(default=None, ge=0, le=1)
    chargeback_count: Optional[int] = Field(default=None, ge=0, le=50)
    delivery_partner_risk: Optional[float] = Field(default=20.0, ge=0.0, le=100.0)
    package_tampered: Optional[int] = Field(default=0, ge=0, le=1)


# ============================================================================
# 4. Analytics & Error Schemas
# ============================================================================

class KPIResponse(BaseModel):
    total_orders: int
    total_spend: float
    total_returns: int
    return_rate: float
    total_refunds: float
    refund_leakage_pct: float
    fraud_loss_intercepted: float
    high_risk_count: int
    high_risk_rate: float
    total_customers: int
    sybil_rings_count: int


class SearchResultItem(BaseModel):
    id: str
    type: str  # "customer", "order", "device", "phone"
    label: str
    subtitle: str
    badge: Optional[str] = None
    risk_hint: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    details: Optional[Any] = None
