"""
RefundShield AI - Pydantic Data Models & Schemas
Standardized serialization for Customer Dossiers, Transactions, Evaluations, and Analytics.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    customer_id: str
    account_age_days: int
    registration_date: str
    gender: Optional[str] = "N/A"
    city: str
    previous_fraud_flag: int
    account_status: str


class CustomerMetrics(BaseModel):
    total_orders: int
    total_spend: float
    avg_order_value: float
    total_returns: int
    return_rate: float
    total_refunds: float
    refund_leakage_pct: float
    chargebacks_count: int
    suspicious_returns_count: int
    categories_bought: List[str] = []
    top_return_reasons: List[str] = []


class DeviceLink(BaseModel):
    device_id: str
    account_count: int = 1


class IdentityFootprint(BaseModel):
    devices: List[DeviceLink] = []
    addresses: List[str] = []
    phones: List[str] = []
    payment_fingerprints: List[str] = []
    is_in_sybil_ring: bool = False
    ring_id: Optional[str] = None
    ring_size: int = 1
    flagged_neighbors_count: int = 0
    syndicate_risk_penalty: float = 0.0
    network_summary: str = "Clean network profile"


class OrderLedgerItem(BaseModel):
    order_id: str
    order_date: str
    category: str
    order_amount: float
    delivery_status: Optional[str] = "Delivered"
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
    hybrid_risk_score: int
    risk_level: str
    recommended_action: str
    badge_color: str
    probable_fraud_type: str
    typology_confidence: float
    rule_score: float
    ml_probability: float
    network_risk_points: float
    ring_size: int = 1
    reasons: List[str] = []
    triggered_rules: List[TriggeredRule] = []


class CustomerDossierResponse(BaseModel):
    customer: CustomerProfile
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


class TransactionEvaluationRequest(BaseModel):
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_amount: Optional[float] = 1500.0
    category: Optional[str] = "Electronics"
    customer_order_count: Optional[int] = None
    customer_return_count: Optional[int] = None
    return_rate: Optional[float] = None
    original_weight_kg: Optional[float] = 1.5
    returned_weight_kg: Optional[float] = 1.5
    item_match_flag: Optional[float] = 1.0
    product_condition: Optional[str] = "Good"
    return_reason: Optional[str] = "Changed mind"
    address_changes: Optional[int] = None
    phone_changes: Optional[int] = None
    device_account_count: Optional[int] = None
    previous_fraud: Optional[int] = None
    chargeback_count: Optional[int] = None
    delivery_partner_risk: Optional[float] = 25.0
    package_tampered: Optional[int] = 0


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


class SearchResult(BaseModel):
    id: str
    type: str  # "customer", "order", "device", "phone"
    label: str
    subtitle: str
    badge: Optional[str] = None
    risk_hint: Optional[str] = None
