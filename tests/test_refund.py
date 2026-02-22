"""
Tests for refund processing to ensure correct refund amounts.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Product, Customer, Order, OrderItem, PromoCode
from services import place_order, process_refund


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_data(db_session):
    """Set up test data: product, customer, and promo code."""
    product = Product(
        id=1,
        name="Test Product",
        description="A test product",
        price=100.00,
        stock=10
    )
    customer = Customer(
        id=1,
        name="Test Customer",
        email="test@example.com",
        loyalty_points=0,
        loyalty_tier="bronze"
    )
    promo = PromoCode(
        id=1,
        code="DISCOUNT20",
        discount_percent=20.0,
        is_active=True,
        min_order_amount=0.0
    )
    db_session.add_all([product, customer, promo])
    db_session.commit()
    return {"product": product, "customer": customer, "promo": promo}


def test_refund_uses_order_total_not_current_price(db_session, setup_data):
    """Test that refund uses order.total, not current product prices."""
    # Place an order at $100
    order = place_order(
        db=db_session,
        customer_id=1,
        items=[{"product_id": 1, "quantity": 1}],
        promo_code_str=None
    )
    assert order.total == 100.00
    original_total = order.total

    # Change the product price after the order
    product = db_session.query(Product).filter(Product.id == 1).first()
    product.price = 150.00  # Price increased
    db_session.commit()

    # Process refund - should refund the original $100, not $150
    result = process_refund(db=db_session, order_id=order.id)

    assert result["refund_amount"] == original_total
    assert result["refund_amount"] == 100.00
    assert result["status"] == "refunded"


def test_refund_with_promo_code_discount(db_session, setup_data):
    """Test that refund reflects the discounted total when promo code was used."""
    # Place an order with 20% discount promo code
    # Product is $100, with 20% off = $80
    order = place_order(
        db=db_session,
        customer_id=1,
        items=[{"product_id": 1, "quantity": 1}],
        promo_code_str="DISCOUNT20"
    )
    assert order.subtotal == 100.00
    assert order.discount_amount == 20.00
    assert order.total == 80.00

    # Process refund - should refund $80 (what customer actually paid)
    result = process_refund(db=db_session, order_id=order.id)

    assert result["refund_amount"] == 80.00
    assert result["status"] == "refunded"


def test_refund_restores_stock(db_session, setup_data):
    """Test that refund restores product stock correctly."""
    product = db_session.query(Product).filter(Product.id == 1).first()
    initial_stock = product.stock  # 10

    # Place an order for 3 items
    order = place_order(
        db=db_session,
        customer_id=1,
        items=[{"product_id": 1, "quantity": 3}],
        promo_code_str=None
    )

    # Stock should be reduced
    db_session.refresh(product)
    assert product.stock == initial_stock - 3  # 7

    # Process refund
    process_refund(db=db_session, order_id=order.id)

    # Stock should be restored
    db_session.refresh(product)
    assert product.stock == initial_stock  # 10


def test_refund_already_refunded_order_raises_error(db_session, setup_data):
    """Test that refunding an already refunded order raises an error."""
    order = place_order(
        db=db_session,
        customer_id=1,
        items=[{"product_id": 1, "quantity": 1}],
        promo_code_str=None
    )

    # First refund should succeed
    process_refund(db=db_session, order_id=order.id)

    # Second refund should fail
    with pytest.raises(ValueError, match="Order already refunded"):
        process_refund(db=db_session, order_id=order.id)


def test_refund_nonexistent_order_raises_error(db_session, setup_data):
    """Test that refunding a non-existent order raises an error."""
    with pytest.raises(ValueError, match="Order not found"):
        process_refund(db=db_session, order_id=9999)


def test_refund_deducts_loyalty_points_correctly(db_session, setup_data):
    """Test that refund deducts loyalty points based on amount paid."""
    customer = db_session.query(Customer).filter(Customer.id == 1).first()
    initial_points = customer.loyalty_points  # 0

    # Place an order with discount ($80 paid)
    order = place_order(
        db=db_session,
        customer_id=1,
        items=[{"product_id": 1, "quantity": 1}],
        promo_code_str="DISCOUNT20"
    )

    # Customer should have earned 80 points (1 per dollar spent)
    db_session.refresh(customer)
    assert customer.loyalty_points == initial_points + 80

    # Process refund
    process_refund(db=db_session, order_id=order.id)

    # Customer should have points deducted (80 points for $80 refund)
    db_session.refresh(customer)
    assert customer.loyalty_points == initial_points  # back to 0
