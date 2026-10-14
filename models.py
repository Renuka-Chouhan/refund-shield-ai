"""
RefundShield AI - SQLAlchemy ORM Relational Models
Enterprise-grade schema with Foreign Keys, Cascade rules, One-to-Many Relationships,
and Composite/B-Tree Indices for high-frequency sub-millisecond query execution.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Index,
    func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    """Customer Dimension Entity."""
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True, doc="Unique Customer Identifier")
    account_age_days = Column(Integer, nullable=False, default=0)
    registration_date = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True, default="N/A")
    city = Column(String(100), nullable=False, index=True)
    previous_fraud_flag = Column(Integer, default=0, index=True, doc="1 = Confirmed Prior Fraud")
    account_status = Column(String(50), default="Active")

    # One-to-Many Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan", lazy="selectin")
    returns = relationship("Return", back_populates="customer", cascade="all, delete-orphan", lazy="selectin")
    devices = relationship("Device", back_populates="customer", cascade="all, delete-orphan", lazy="selectin")
    identity_links = relationship("IdentityLink", back_populates="customer", cascade="all, delete-orphan", lazy="selectin")
    fraud_evaluations = relationship("FraudEvaluation", back_populates="customer", lazy="selectin")

    __table_args__ = (
        Index("idx_customer_city_fraud", "city", "previous_fraud_flag"),
    )


class Merchant(Base):
    """Merchant Dimension Entity."""
    __tablename__ = "merchants"

    merchant_id = Column(String(50), primary_key=True, index=True)
    category = Column(String(100), nullable=True)
    total_orders = Column(Integer, default=0)
    return_rate = Column(Float, default=0.0)
    refund_rate = Column(Float, default=0.0)
    fraud_rate = Column(Float, default=0.0)
    merchant_risk_score = Column(Integer, default=0)

    orders = relationship("Order", back_populates="merchant")


class DeliveryPartner(Base):
    """Logistics and Courier Partner Dimension Entity."""
    __tablename__ = "delivery_partners"

    delivery_partner_id = Column(String(50), primary_key=True, index=True)
    total_deliveries = Column(Integer, default=0)
    return_complaints = Column(Integer, default=0)
    tampering_cases = Column(Integer, default=0)
    suspicious_returns = Column(Integer, default=0)
    partner_risk_score = Column(Integer, default=0)

    deliveries = relationship("Delivery", back_populates="delivery_partner")


class Order(Base):
    """Core Orders Fact Table."""
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    product_id = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    order_amount = Column(Float, nullable=False)
    order_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, default=1)
    discount_amount = Column(Float, default=0.0)
    payment_id = Column(String(50), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    merchant = relationship("Merchant", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    delivery = relationship("Delivery", back_populates="order", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    return_record = relationship("Return", back_populates="order", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
    fraud_evaluations = relationship("FraudEvaluation", back_populates="order")

    __table_args__ = (
        Index("idx_orders_cust_date", "customer_id", "order_date"),
    )


class Payment(Base):
    """Payment Transactions Fact Table."""
    __tablename__ = "payments"

    payment_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    payment_method = Column(String(50), nullable=False)
    payment_amount = Column(Float, nullable=False)
    payment_status = Column(String(50), default="Success")
    chargeback_flag = Column(Integer, default=0, index=True)
    chargeback_amount = Column(Float, default=0.0)
    payment_attempts = Column(Integer, default=1)

    order = relationship("Order", back_populates="payment")


class Delivery(Base):
    """Fulfillment and Carrier Telemetry Fact Table."""
    __tablename__ = "deliveries"

    delivery_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    delivery_partner_id = Column(String(50), ForeignKey("delivery_partners.delivery_partner_id"), nullable=False, index=True)
    delivery_date = Column(Date, nullable=False)
    delivery_status = Column(String(50), default="Delivered")
    original_weight_kg = Column(Float, nullable=False)
    package_tampered = Column(Integer, default=0)
    delivery_location_id = Column(String(50), nullable=True)

    order = relationship("Order", back_populates="delivery")
    delivery_partner = relationship("DeliveryPartner", back_populates="deliveries")


class Return(Base):
    """Returns and Physical Package Inspection Fact Table."""
    __tablename__ = "returns"

    return_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    return_date = Column(Date, nullable=False)
    return_reason = Column(String(100), nullable=True)
    return_status = Column(String(50), default="Received")
    returned_weight_kg = Column(Float, nullable=False)
    product_condition = Column(String(50), default="Good")
    item_match_flag = Column(Integer, default=1, doc="1 = Barcode/SKU Match, 0 = Counterfeit/Swap")
    packaging_condition = Column(String(50), default="Intact")

    order = relationship("Order", back_populates="return_record")
    customer = relationship("Customer", back_populates="returns")
    refund = relationship("Refund", back_populates="return_record", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class Refund(Base):
    """Refund Disbursement Fact Table."""
    __tablename__ = "refunds"

    refund_id = Column(String(50), primary_key=True, index=True)
    return_id = Column(String(50), ForeignKey("returns.return_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    refund_amount = Column(Float, nullable=False)
    refund_date = Column(Date, nullable=False)
    refund_status = Column(String(50), default="Approved")
    refund_method = Column(String(50), nullable=True)
    manual_review_flag = Column(Integer, default=0)

    return_record = relationship("Return", back_populates="refund")
    order = relationship("Order", back_populates="refunds")


class Device(Base):
    """Hardware Device Association Bridge Table."""
    __tablename__ = "devices"

    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), primary_key=True)
    device_id = Column(String(50), primary_key=True, index=True)
    first_seen_date = Column(Date, nullable=True)
    last_seen_date = Column(Date, nullable=True)
    account_count = Column(Integer, default=1, index=True, doc="Count of distinct accounts sharing this device")

    customer = relationship("Customer", back_populates="devices")


class IdentityLink(Base):
    """Identity Graph Relationships Bridge Table."""
    __tablename__ = "identity_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    address_id = Column(String(50), nullable=True, index=True)
    phone_hash = Column(String(50), nullable=True, index=True)
    device_id = Column(String(50), nullable=True, index=True)
    payment_fingerprint = Column(String(50), nullable=True, index=True)

    customer = relationship("Customer", back_populates="identity_links")


class FraudEvaluation(Base):
    """Live Fraud Risk Evaluation Audit Trail."""
    __tablename__ = "fraud_evaluations"

    evaluation_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    rule_score = Column(Float, nullable=False)
    ml_probability = Column(Float, nullable=False)
    hybrid_risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    recommended_action = Column(String(50), nullable=False)
    predicted_fraud_type = Column(String(100), nullable=False)
    triggered_rules_json = Column(Text, nullable=True)
    evaluation_timestamp = Column(DateTime, server_default=func.now(), index=True)

    customer = relationship("Customer", back_populates="fraud_evaluations")
    order = relationship("Order", back_populates="fraud_evaluations")
