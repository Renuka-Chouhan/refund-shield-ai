"""
RefundShield AI - Order Investigation & Risk Evaluation Service
Uses SQLAlchemy ORM for relational joins and executes live hybrid fraud scoring.
"""

from typing import Optional
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Order, Customer, Merchant, Delivery, DeliveryPartner, Return, Refund, Payment
from schemas import OrderDetailsResponse, FraudRiskEvaluation, TriggeredRule
from src.scoring.hybrid_engine import HybridFraudEngine
from src.graph.network_analyzer import IdentityNetworkAnalyzer


def get_order_details(
    order_id: str,
    hybrid_engine: HybridFraudEngine,
    network_analyzer: IdentityNetworkAnalyzer,
    db: Optional[Session] = None
) -> Optional[OrderDetailsResponse]:
    """
    Retrieves full relational context for an order and evaluates live fraud risk using SQLAlchemy.
    """
    oid = str(order_id).strip().upper()
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        order: Optional[Order] = db.query(Order).filter(Order.order_id == oid).first()
        if not order:
            return None

        cust = order.customer
        cid = cust.customer_id if cust else "UNKNOWN"
        merchant = order.merchant
        delivery = order.delivery
        ret = order.return_record
        refund = ret.refund if ret else None
        payment = order.payment

        # Historical customer metrics for baseline evaluation
        c_orders = len(cust.orders) if cust else 1
        c_returns = len(cust.returns) if cust else 0
        ret_rate = round((c_returns / max(1, c_orders)) * 100.0, 1)

        max_dev_acc = 1
        if cust and cust.devices:
            max_dev_acc = max([d.account_count for d in cust.devices] or [1])

        orig_wt = float(delivery.original_weight_kg) if delivery and delivery.original_weight_kg is not None else 1.0
        ret_wt = float(ret.returned_weight_kg) if ret and ret.returned_weight_kg is not None else orig_wt
        wt_loss = 0.0
        if orig_wt > 0 and ret_wt is not None:
            wt_loss = max(0.0, round(((orig_wt - ret_wt) / orig_wt) * 100.0, 1))

        item_match = float(ret.item_match_flag) if ret and ret.item_match_flag is not None else 1.0
        prod_cond = str(ret.product_condition) if ret and ret.product_condition else "Good"

        partner_risk = float(delivery.delivery_partner.partner_risk_score) if delivery and delivery.delivery_partner else 20.0
        m_rate = float(merchant.return_rate) if merchant else 15.0
        amt = float(order.order_amount)

        order_eval_input = {
            "order_id": oid,
            "customer_id": cid,
            "order_amount": amt,
            "category": str(order.category),
            "customer_order_count": c_orders,
            "customer_return_count": c_returns,
            "return_rate": ret_rate,
            "original_weight_kg": orig_wt,
            "returned_weight_kg": ret_wt,
            "weight_difference_pct": wt_loss,
            "item_match_flag": item_match,
            "product_condition": prod_cond,
            "return_reason": str(ret.return_reason) if ret and ret.return_reason else "None",
            "address_changes": 0,
            "phone_changes": 0,
            "device_account_count": max_dev_acc,
            "previous_fraud": int(cust.previous_fraud_flag) if cust else 0,
            "chargeback_count": int(payment.chargeback_flag) if payment and payment.chargeback_flag else 0,
            "delivery_partner_risk": partner_risk,
            "merchant_return_rate": m_rate,
            "package_tampered": int(delivery.package_tampered) if delivery else 0
        }

        eval_res = hybrid_engine.evaluate_transaction(order_eval_input, persist_audit=True)

        risk_evaluation = FraudRiskEvaluation(
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

        delivery_info = {
            "delivery_id": delivery.delivery_id if delivery else None,
            "delivery_partner_id": delivery.delivery_partner_id if delivery else None,
            "delivery_status": delivery.delivery_status if delivery else "Delivered",
            "delivery_date": str(delivery.delivery_date) if delivery and delivery.delivery_date else None,
            "original_weight_kg": orig_wt,
            "package_tampered": delivery.package_tampered if delivery else 0,
            "partner_risk_score": partner_risk
        }

        return_info = None
        if ret:
            return_info = {
                "return_id": ret.return_id,
                "return_date": str(ret.return_date),
                "return_reason": ret.return_reason,
                "return_status": ret.return_status,
                "returned_weight_kg": ret_wt,
                "weight_loss_pct": wt_loss,
                "product_condition": prod_cond,
                "item_match_flag": item_match,
                "packaging_condition": ret.packaging_condition
            }

        refund_info = None
        if refund:
            refund_info = {
                "refund_id": refund.refund_id,
                "refund_amount": float(refund.refund_amount),
                "refund_status": refund.refund_status,
                "refund_date": str(refund.refund_date) if refund.refund_date else None
            }

        payment_info = {
            "payment_id": payment.payment_id if payment else None,
            "payment_method": payment.payment_method if payment else None,
            "payment_status": payment.payment_status if payment else None,
            "chargeback_flag": payment.chargeback_flag if payment else 0
        }

        customer_summary = {
            "customer_id": cid,
            "city": cust.city if cust else None,
            "account_age_days": cust.account_age_days if cust else 0,
            "previous_fraud_flag": cust.previous_fraud_flag if cust else 0,
            "account_status": cust.account_status if cust else "Active",
            "customer_order_count": c_orders,
            "customer_return_count": c_returns,
            "return_rate": ret_rate
        }

        return OrderDetailsResponse(
            order_id=oid,
            customer_id=cid,
            merchant_id=order.merchant_id,
            product_id=order.product_id,
            category=order.category,
            order_amount=amt,
            order_date=str(order.order_date),
            delivery=delivery_info,
            return_info=return_info,
            refund_info=refund_info,
            payment=payment_info,
            customer_summary=customer_summary,
            risk_evaluation=risk_evaluation
        )

    finally:
        if close_session:
            db.close()
