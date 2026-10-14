"""
RefundShield AI - Customer Investigation & Dynamic Profiling Service
High-performance relational extraction using SQLAlchemy models and relationships.
Compiles real-time behavioral ledgers, evaluates identity syndicate graphs, and executes multi-layer fraud scoring.
"""

from typing import Dict, Any, List, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from models import Customer, Order, Return, Refund, Payment, Device, IdentityLink
from schemas import (
    CustomerBase,
    CustomerMetrics,
    DeviceLink,
    IdentityFootprint,
    OrderLedgerItem,
    TriggeredRule,
    FraudRiskEvaluation,
    CustomerLookupResponse
)
from src.scoring.hybrid_engine import HybridFraudEngine
from src.graph.network_analyzer import IdentityNetworkAnalyzer


def get_customer_dossier(
    customer_id: str,
    hybrid_engine: HybridFraudEngine,
    network_analyzer: IdentityNetworkAnalyzer,
    db: Optional[Session] = None
) -> Optional[CustomerLookupResponse]:
    """
    Dynamically loads and evaluates full customer profile, transaction history,
    identity links, and live hybrid risk score using SQLAlchemy ORM.
    """
    cid = str(customer_id).strip().upper()
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # 1. Fetch customer master record with eager loaded relationships
        cust: Optional[Customer] = db.query(Customer).filter(Customer.customer_id == cid).first()
        if not cust:
            return None

        customer_profile = CustomerBase(
            customer_id=cust.customer_id,
            account_age_days=cust.account_age_days,
            registration_date=cust.registration_date,
            gender=cust.gender or "N/A",
            city=cust.city,
            previous_fraud_flag=cust.previous_fraud_flag,
            account_status=cust.account_status or "Active"
        )

        # 2. Build orders ledger and calculate behavioral metrics
        orders_list: List[OrderLedgerItem] = []
        categories = []
        return_reasons = []
        total_spend = 0.0
        total_refunds = 0.0
        returns_count = 0
        chargebacks_count = 0
        suspicious_returns_count = 0
        has_sku_mismatch = False
        has_missing_condition = False
        has_used_condition = False
        worst_weight_loss_pct = 0.0

        for o in cust.orders:
            amt = float(o.order_amount or 0.0)
            total_spend += amt
            cat = str(o.category or "General")
            categories.append(cat)

            delivery = o.delivery
            orig_wt = float(delivery.original_weight_kg) if delivery and delivery.original_weight_kg is not None else None
            courier_id = delivery.delivery_partner_id if delivery else None
            del_status = delivery.delivery_status if delivery else "Delivered"

            ret = o.return_record
            ret_wt = None
            wt_loss = None
            ret_reason = None
            prod_cond = None
            item_match = 1.0

            if ret:
                returns_count += 1
                ret_reason = ret.return_reason
                if ret_reason:
                    return_reasons.append(str(ret_reason))

                ret_wt = float(ret.returned_weight_kg) if ret.returned_weight_kg is not None else None
                if orig_wt and ret_wt is not None and orig_wt > 0:
                    wt_loss = max(0.0, round(((orig_wt - ret_wt) / orig_wt) * 100.0, 1))
                    if wt_loss > worst_weight_loss_pct:
                        worst_weight_loss_pct = wt_loss

                prod_cond = str(ret.product_condition) if ret.product_condition else "Good"
                cond_lower = prod_cond.lower()
                if "missing" in cond_lower or "empty" in cond_lower:
                    has_missing_condition = True
                    suspicious_returns_count += 1
                elif "used" in cond_lower:
                    has_used_condition = True
                    suspicious_returns_count += 1

                item_match = float(ret.item_match_flag) if ret.item_match_flag is not None else 1.0
                if item_match == 0.0:
                    has_sku_mismatch = True
                    suspicious_returns_count += 1

                if wt_loss and wt_loss >= 25.0:
                    suspicious_returns_count += 1

            # Refund info
            ref = ret.refund if ret else None
            ref_amt = float(ref.refund_amount) if ref and ref.refund_amount is not None else None
            ref_status = ref.refund_status if ref else None
            if ref_amt:
                total_refunds += ref_amt

            # Payment info
            pay = o.payment
            pay_method = pay.payment_method if pay else None
            cb_flag = int(pay.chargeback_flag) if pay and pay.chargeback_flag is not None else 0
            if cb_flag == 1:
                chargebacks_count += 1

            orders_list.append(OrderLedgerItem(
                order_id=o.order_id,
                order_date=str(o.order_date),
                category=cat,
                order_amount=round(amt, 2),
                delivery_status=del_status,
                courier_id=courier_id,
                original_weight_kg=orig_wt,
                returned_weight_kg=ret_wt,
                weight_loss_pct=wt_loss,
                return_reason=ret_reason,
                product_condition=prod_cond,
                item_match_flag=item_match,
                refund_amount=round(ref_amt, 2) if ref_amt else None,
                refund_status=ref_status,
                payment_method=pay_method,
                chargeback_flag=cb_flag
            ))

        total_orders = len(orders_list)
        return_rate = round((returns_count / max(1, total_orders)) * 100.0, 1)
        refund_leakage = round((total_refunds / max(1.0, total_spend)) * 100.0, 1)
        avg_aov = round(total_spend / max(1, total_orders), 2)

        top_reasons = [reason for reason, _ in Counter(return_reasons).most_common(3)]
        top_categories = list(dict.fromkeys(categories))[:4]

        metrics = CustomerMetrics(
            total_orders=total_orders,
            total_spend=round(total_spend, 2),
            avg_order_value=avg_aov,
            total_returns=returns_count,
            return_rate=return_rate,
            total_refunds=round(total_refunds, 2),
            refund_leakage_pct=refund_leakage,
            chargebacks_count=chargebacks_count,
            suspicious_returns_count=suspicious_returns_count,
            categories_bought=top_categories,
            top_return_reasons=top_reasons
        )

        # 3. Identity Footprint & Devices
        devices_list: List[DeviceLink] = []
        max_dev_accounts = 1
        for d in cust.devices:
            ac_cnt = int(d.account_count or 1)
            max_dev_accounts = max(max_dev_accounts, ac_cnt)
            devices_list.append(DeviceLink(device_id=d.device_id, account_count=ac_cnt))

        addresses = list({link.address_id for link in cust.identity_links if link.address_id})
        phones = list({link.phone_hash for link in cust.identity_links if link.phone_hash})
        fingerprints = list({link.payment_fingerprint for link in cust.identity_links if link.payment_fingerprint})

        # Evaluate Network Risk via NetworkX Analyzer
        net_eval = network_analyzer.evaluate_customer_network_risk(cid)
        rings = network_analyzer.find_fraud_rings(min_accounts=2)
        matched_ring_id = None
        for ring in rings:
            if cid in ring["customers"]:
                matched_ring_id = ring["ring_id"]
                break

        identity = IdentityFootprint(
            devices=devices_list,
            addresses=addresses,
            phones=phones,
            payment_fingerprints=fingerprints,
            is_in_sybil_ring=net_eval.get("is_in_sybil_ring", False),
            ring_id=matched_ring_id,
            ring_size=net_eval.get("ring_size", 1),
            flagged_neighbors_count=net_eval.get("flagged_connected_accounts", 0),
            syndicate_risk_penalty=float(net_eval.get("network_risk_points", 0.0)),
            network_summary=net_eval.get("description", "Clean profile")
        )

        # 4. Multi-Layer Dynamic Risk Scoring
        primary_cat = categories[0] if categories else "Electronics"
        prod_cond = "Missing" if has_missing_condition else ("Used" if has_used_condition else "Good")
        item_match_flag = 0.0 if has_sku_mismatch else 1.0

        synth_transaction = {
            "order_id": f"LIVE_{cid}_{orders_list[0].order_id if orders_list else 'NEW'}",
            "customer_id": cid,
            "order_amount": avg_aov if avg_aov > 0 else 2500.0,
            "category": primary_cat,
            "customer_order_count": max(1, total_orders),
            "customer_return_count": returns_count,
            "return_rate": return_rate,
            "original_weight_kg": 2.5,
            "returned_weight_kg": 2.5 * (1.0 - (worst_weight_loss_pct / 100.0)),
            "weight_difference_pct": worst_weight_loss_pct,
            "item_match_flag": item_match_flag,
            "product_condition": prod_cond,
            "return_reason": top_reasons[0] if top_reasons else "Changed mind",
            "address_changes": max(0, len(addresses) - 1),
            "phone_changes": max(0, len(phones) - 1),
            "device_account_count": max_dev_accounts,
            "previous_fraud": customer_profile.previous_fraud_flag,
            "chargeback_count": chargebacks_count,
            "delivery_partner_risk": 20.0,
            "account_age_days": customer_profile.account_age_days
        }

        eval_res = hybrid_engine.evaluate_transaction(synth_transaction, persist_audit=False)

        risk_evaluation = FraudRiskEvaluation(
            order_id=eval_res["order_id"],
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

        return CustomerLookupResponse(
            customer=customer_profile,
            metrics=metrics,
            identity=identity,
            risk_evaluation=risk_evaluation,
            orders=orders_list
        )

    finally:
        if close_session:
            db.close()


def list_customers_summary(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    risk_filter: str = "",
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Returns paginated customer summary records for directory navigation.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        query = db.query(Customer)
        if search:
            s = f"%{search.strip().upper()}%"
            query = query.filter((Customer.customer_id.ilike(s)) | (Customer.city.ilike(s)))

        total_count = query.count()
        offset = (page - 1) * limit
        customers_rows = query.order_by(Customer.previous_fraud_flag.desc()).offset(offset).limit(limit).all()

        customers = []
        for c in customers_rows:
            o_cnt = len(c.orders)
            r_cnt = len(c.returns)
            ret_rate = round((r_cnt / max(1, o_cnt)) * 100.0, 1)
            spend = round(sum(o.order_amount for o in c.orders), 2)
            prev_fraud = int(c.previous_fraud_flag or 0)

            if prev_fraud == 1 or ret_rate >= 70:
                tier = "High"
                tier_color = "#EF4444"
            elif ret_rate >= 35 or o_cnt >= 10:
                tier = "Medium"
                tier_color = "#F59E0B"
            else:
                tier = "Low"
                tier_color = "#10B981"

            if risk_filter and tier.lower() != risk_filter.lower():
                continue

            customers.append({
                "customer_id": c.customer_id,
                "account_age_days": c.account_age_days,
                "registration_date": str(c.registration_date),
                "city": c.city,
                "previous_fraud_flag": prev_fraud,
                "account_status": c.account_status,
                "total_orders": o_cnt,
                "total_returns": r_cnt,
                "return_rate": ret_rate,
                "total_spend": spend,
                "risk_tier": tier,
                "tier_color": tier_color
            })

        return {
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // max(1, limit),
            "customers": customers
        }
    finally:
        if close_session:
            db.close()
