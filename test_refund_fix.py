"""
Test for the refund bug fix.

Verifies that refunds use the original order total instead of current product prices.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Customer, Order, OrderItem
from services import place_order, process_refund


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def test_data(db_session):
    """Set up test data."""
    # Create a customer
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        loyalty_points=100,
        loyalty_tier="bronze"
    )
    db_session.add(customer)
    
    # Create a product
    product = Product(
        name="Test Product",
        description="A test product",
        price=50.00,
        stock=10
    )
    db_session.add(product)
    
    db_session.commit()
    db_session.refresh(customer)
    db_session.refresh(product)
    
    return {"customer": customer, "product": product}


def test_refund_uses_order_total_not_current_price(db_session, test_data):
    """Test that refunds use the order total, not current product prices."""
    customer = test_data["customer"]
    product = test_data["product"]
    
    # Place an order at the original price
    original_price = 50.00
    assert product.price == original_price
    
    order = place_order(
        db=db_session,
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 2}]
    )
    
    # Verify order was placed correctly
    assert order.total == 100.00  # 2 * $50.00
    assert product.stock == 8  # 10 - 2
    
    # Change the product price AFTER the order was placed
    new_price = 75.00
    product.price = new_price
    db_session.commit()
    
    # Process the refund
    refund_result = process_refund(db=db_session, order_id=order.id)
    
    # Verify refund amount matches the original order total, not current price
    assert refund_result["refund_amount"] == 100.00  # Original total
    assert refund_result["refund_amount"] != 150.00  # NOT current price * quantity
    assert refund_result["status"] == "refunded"
    
    # Verify stock was restored
    db_session.refresh(product)
    assert product.stock == 10  # Back to original stock
    
    # Verify order status updated
    db_session.refresh(order)
    assert order.status == "refunded"
    assert order.refund_amount == 100.00
    
    # Verify loyalty points were deducted correctly
    db_session.refresh(customer)
    # Original: 100 + 100 (from order) - 100 (from refund) = 100
    assert customer.loyalty_points == 100


def test_refund_with_zero_stock_product(db_session, test_data):
    """Test refund when product stock is zero (edge case)."""
    customer = test_data["customer"]
    product = test_data["product"]
    
    # Place an order that uses all stock
    order = place_order(
        db=db_session,
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 10}]  # Use all stock
    )
    
    assert product.stock == 0
    assert order.total == 500.00  # 10 * $50.00
    
    # Change price after order
    product.price = 25.00  # Much lower price
    db_session.commit()
    
    # Process refund
    refund_result = process_refund(db=db_session, order_id=order.id)
    
    # Should still refund the original amount, not recalculated amount
    assert refund_result["refund_amount"] == 500.00  # Original total
    assert refund_result["refund_amount"] != 250.00  # NOT current price * quantity
    
    # Stock should be restored
    db_session.refresh(product)
    assert product.stock == 10


def test_refund_already_refunded_order(db_session, test_data):
    """Test that refunding an already refunded order raises an error."""
    customer = test_data["customer"]
    product = test_data["product"]
    
    # Place and refund an order
    order = place_order(
        db=db_session,
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}]
    )
    
    process_refund(db=db_session, order_id=order.id)
    
    # Try to refund again - should raise ValueError
    with pytest.raises(ValueError, match="Order already refunded"):
        process_refund(db=db_session, order_id=order.id)
