-- ====================================================================
-- RefundShield AI: Analytical SQL Queries for Fraud Investigators
-- Industry-grade detection queries across multi-entity relationships
-- ====================================================================

-- 1. Serial Returners: Identify customers with return rate > 60% and at least 3 orders
SELECT 
    c.customer_id,
    c.city,
    c.account_age_days,
    COUNT(o.order_id) AS total_orders,
    COUNT(r.return_id) AS total_returns,
    ROUND(CAST(COUNT(r.return_id) AS REAL) / COUNT(o.order_id) * 100.0, 2) AS return_rate_pct,
    ROUND(SUM(o.order_amount), 2) AS total_spend,
    ROUND(COALESCE(SUM(rf.refund_amount), 0), 2) AS total_refunded
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN returns r ON o.order_id = r.order_id
LEFT JOIN refunds rf ON r.return_id = rf.return_id
GROUP BY c.customer_id, c.city, c.account_age_days
HAVING COUNT(o.order_id) >= 2 AND (CAST(COUNT(r.return_id) AS REAL) / COUNT(o.order_id)) >= 0.50
ORDER BY return_rate_pct DESC, total_refunded DESC;

-- 2. Multi-Account Device Ring Detection (Sybil Accounts)
-- Detects hardware devices linked to multiple distinct customer accounts
SELECT 
    il.device_id,
    COUNT(DISTINCT il.customer_id) AS linked_accounts_count,
    GROUP_CONCAT(DISTINCT il.customer_id) AS customer_ids,
    GROUP_CONCAT(DISTINCT il.phone_hash) AS phone_hashes,
    COUNT(DISTINCT r.return_id) AS total_returns_across_ring,
    ROUND(COALESCE(SUM(rf.refund_amount), 0), 2) AS total_refunded_across_ring
FROM identity_links il
LEFT JOIN orders o ON il.customer_id = o.customer_id
LEFT JOIN returns r ON o.order_id = r.order_id
LEFT JOIN refunds rf ON r.return_id = rf.return_id
GROUP BY il.device_id
HAVING COUNT(DISTINCT il.customer_id) >= 2
ORDER BY linked_accounts_count DESC, total_refunded_across_ring DESC;

-- 3. Empty Box / Significant Weight Discrepancy Detection
-- Flags returns where outbound delivery weight and returned package weight differ by > 30%
SELECT 
    r.return_id,
    r.order_id,
    r.customer_id,
    d.original_weight_kg,
    r.returned_weight_kg,
    ROUND(((d.original_weight_kg - r.returned_weight_kg) / d.original_weight_kg) * 100.0, 2) AS weight_loss_pct,
    r.return_reason,
    r.product_condition,
    o.order_amount
FROM returns r
JOIN deliveries d ON r.order_id = d.order_id
JOIN orders o ON r.order_id = o.order_id
WHERE (d.original_weight_kg - r.returned_weight_kg) / d.original_weight_kg >= 0.25
ORDER BY weight_loss_pct DESC;

-- 4. Wardrobing Suspects: High-value fashion returns marked as 'Used' or rapid return
SELECT 
    o.order_id,
    o.customer_id,
    o.category,
    o.order_amount,
    d.delivery_date,
    r.return_date,
    ROUND(JULIANDAY(r.return_date) - JULIANDAY(d.delivery_date), 1) AS days_to_return,
    r.product_condition,
    r.return_reason
FROM orders o
JOIN deliveries d ON o.order_id = d.order_id
JOIN returns r ON o.order_id = r.order_id
WHERE o.category = 'Fashion' 
  AND (r.product_condition = 'Used' OR (JULIANDAY(r.return_date) - JULIANDAY(d.delivery_date) <= 3))
ORDER BY o.order_amount DESC;

-- 5. Delivery Partner Collusion / Route Tampering Anomaly
-- Identifies delivery partners with disproportionate tampering cases and returns
SELECT 
    dp.delivery_partner_id,
    dp.total_deliveries,
    dp.tampering_cases,
    dp.suspicious_returns,
    dp.partner_risk_score,
    COUNT(d.delivery_id) AS current_deliveries,
    SUM(d.package_tampered) AS active_tampered_packages,
    COUNT(r.return_id) AS returns_associated
FROM delivery_partners dp
LEFT JOIN deliveries d ON dp.delivery_partner_id = d.delivery_partner_id
LEFT JOIN returns r ON d.order_id = r.order_id
GROUP BY dp.delivery_partner_id
ORDER BY dp.partner_risk_score DESC, dp.tampering_cases DESC;

-- 6. Friendly Fraud / Chargeback-after-Refund Double Dipping
-- Detects orders where a refund was issued AND a payment chargeback was filed
SELECT 
    p.order_id,
    o.customer_id,
    p.payment_amount,
    p.chargeback_flag,
    p.chargeback_amount,
    rf.refund_amount,
    rf.refund_status,
    (p.chargeback_amount + rf.refund_amount) AS total_financial_leakage
FROM payments p
JOIN orders o ON p.order_id = o.order_id
JOIN refunds rf ON o.order_id = rf.order_id
WHERE p.chargeback_flag = 1
ORDER BY total_financial_leakage DESC;

-- 7. High-Risk Merchant Return & Refund Leakage
-- Identifies merchant accounts exhibiting abnormal customer disputes
SELECT 
    m.merchant_id,
    m.category,
    m.total_orders,
    m.return_rate AS historical_return_rate_pct,
    m.fraud_rate AS historical_fraud_rate_pct,
    m.merchant_risk_score,
    COUNT(o.order_id) AS recent_orders,
    COUNT(r.return_id) AS recent_returns,
    ROUND(COALESCE(SUM(rf.refund_amount), 0), 2) AS total_refund_payout
FROM merchants m
LEFT JOIN orders o ON m.merchant_id = o.merchant_id
LEFT JOIN returns r ON o.order_id = r.order_id
LEFT JOIN refunds rf ON r.return_id = rf.return_id
GROUP BY m.merchant_id
ORDER BY m.merchant_risk_score DESC;

-- 8. Rapid Identity Velocity (Address & Phone Mutation)
-- Identifies customers associated with multiple shipping addresses or phones
SELECT 
    il.customer_id,
    c.account_age_days,
    COUNT(DISTINCT il.address_id) AS distinct_addresses,
    COUNT(DISTINCT il.phone_hash) AS distinct_phones,
    COUNT(DISTINCT il.device_id) AS distinct_devices,
    COUNT(DISTINCT il.payment_fingerprint) AS distinct_payment_methods
FROM identity_links il
JOIN customers c ON il.customer_id = c.customer_id
GROUP BY il.customer_id
HAVING COUNT(DISTINCT il.address_id) > 1 OR COUNT(DISTINCT il.phone_hash) > 1
ORDER BY distinct_addresses DESC, distinct_phones DESC;

-- 9. Item Switching / Packaging Inspection Failures
-- Inspects returns where returned product was mismatched with manifest
SELECT 
    r.return_id,
    r.order_id,
    r.customer_id,
    o.product_id,
    o.category,
    o.order_amount,
    r.item_match_flag,
    r.packaging_condition,
    r.return_reason
FROM returns r
JOIN orders o ON r.order_id = o.order_id
WHERE r.item_match_flag = 0
ORDER BY o.order_amount DESC;

-- 10. Executive Fraud Loss & Recovery Summary
SELECT 
    COUNT(DISTINCT o.order_id) AS total_orders_evaluated,
    COUNT(DISTINCT r.return_id) AS total_returns_requested,
    COUNT(DISTINCT rf.refund_id) AS total_refunds_processed,
    ROUND(SUM(o.order_amount), 2) AS total_order_volume,
    ROUND(SUM(rf.refund_amount), 2) AS total_refund_volume,
    ROUND(SUM(CASE WHEN rf.manual_review_flag = 1 THEN rf.refund_amount ELSE 0 END), 2) AS flagged_refund_volume
FROM orders o
LEFT JOIN returns r ON o.order_id = r.order_id
LEFT JOIN refunds rf ON r.return_id = rf.return_id;
