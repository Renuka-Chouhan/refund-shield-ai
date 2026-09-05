-- ====================================================================
-- RefundShield AI: E-Commerce Refund & Return Fraud Detection Database
-- Database Schema (SQLite / PostgreSQL compatible)
-- ====================================================================

-- 1. Customers Dimension
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    account_age_days INTEGER NOT NULL,
    registration_date DATE NOT NULL,
    gender VARCHAR(10),
    city VARCHAR(100),
    previous_fraud_flag INTEGER DEFAULT 0,
    account_status VARCHAR(50) DEFAULT 'Active'
);

-- 2. Merchants Dimension
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100),
    total_orders INTEGER DEFAULT 0,
    return_rate REAL DEFAULT 0.0,
    refund_rate REAL DEFAULT 0.0,
    fraud_rate REAL DEFAULT 0.0,
    merchant_risk_score INTEGER DEFAULT 0
);

-- 3. Delivery Partners Dimension
CREATE TABLE IF NOT EXISTS delivery_partners (
    delivery_partner_id VARCHAR(50) PRIMARY KEY,
    total_deliveries INTEGER DEFAULT 0,
    return_complaints INTEGER DEFAULT 0,
    tampering_cases INTEGER DEFAULT 0,
    suspicious_returns INTEGER DEFAULT 0,
    partner_risk_score INTEGER DEFAULT 0
);

-- 4. Orders Fact Table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    merchant_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    order_amount REAL NOT NULL,
    order_date DATE NOT NULL,
    quantity INTEGER DEFAULT 1,
    discount_amount REAL DEFAULT 0.0,
    payment_id VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

-- 5. Payments Fact Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_amount REAL NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'Success',
    chargeback_flag INTEGER DEFAULT 0,
    chargeback_amount REAL DEFAULT 0.0,
    payment_attempts INTEGER DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 6. Deliveries Fact Table
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    delivery_partner_id VARCHAR(50) NOT NULL,
    delivery_date DATE NOT NULL,
    delivery_status VARCHAR(50) DEFAULT 'Delivered',
    original_weight_kg REAL NOT NULL,
    package_tampered INTEGER DEFAULT 0,
    delivery_location_id VARCHAR(50),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(delivery_partner_id)
);

-- 7. Returns Fact Table
CREATE TABLE IF NOT EXISTS returns (
    return_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    return_date DATE NOT NULL,
    return_reason VARCHAR(100),
    return_status VARCHAR(50) DEFAULT 'Received',
    returned_weight_kg REAL NOT NULL,
    product_condition VARCHAR(50) DEFAULT 'Good',
    item_match_flag INTEGER DEFAULT 1,
    packaging_condition VARCHAR(50) DEFAULT 'Intact',
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 8. Refunds Fact Table
CREATE TABLE IF NOT EXISTS refunds (
    refund_id VARCHAR(50) PRIMARY KEY,
    return_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    refund_amount REAL NOT NULL,
    refund_date DATE NOT NULL,
    refund_status VARCHAR(50) DEFAULT 'Approved',
    refund_method VARCHAR(50),
    manual_review_flag INTEGER DEFAULT 0,
    FOREIGN KEY (return_id) REFERENCES returns(return_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 9. Devices Bridge Table
CREATE TABLE IF NOT EXISTS devices (
    customer_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    first_seen_date DATE,
    last_seen_date DATE,
    account_count INTEGER DEFAULT 1,
    PRIMARY KEY (customer_id, device_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 10. Identity Links Bridge Table
CREATE TABLE IF NOT EXISTS identity_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id VARCHAR(50) NOT NULL,
    address_id VARCHAR(50),
    phone_hash VARCHAR(50),
    device_id VARCHAR(50),
    payment_fingerprint VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 11. Fraud Risk Evaluations Audit Log Table
CREATE TABLE IF NOT EXISTS fraud_evaluations (
    evaluation_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    rule_score REAL NOT NULL,
    ml_probability REAL NOT NULL,
    hybrid_risk_score REAL NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    recommended_action VARCHAR(50) NOT NULL,
    predicted_fraud_type VARCHAR(100) NOT NULL,
    triggered_rules_json TEXT,
    evaluation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Indices for performance optimization
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_merchant ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_returns_customer ON returns(customer_id);
CREATE INDEX IF NOT EXISTS idx_returns_order ON returns(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_order ON deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_identity_device ON identity_links(device_id);
CREATE INDEX IF NOT EXISTS idx_identity_phone ON identity_links(phone_hash);
