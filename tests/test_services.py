import pytest
from yourapp.services import process_refund
from yourapp.models import Order, OrderItem, Product

@pytest.fixture
def setup_order_with_items(db_session):
    # Setup: Create a product, an order with an item at a specific price_at_purchase
    product = Product(price=10.0)
    db_session.add(product)
    db_session.flush()
    order = Order()
    order_item = OrderItem(product_id=product.id, quantity=2, price_at_purchase=5.0)  # Price at purchase is different from current product price
    order.order_items.append(order_item)
    db_session.add(order)
    db_session.flush()
    yield order
    db_session.delete(order)
    db_session.delete(product)
    db_session.commit()

def test_refund_calculation_price_at_purchase(setup_order_with_items):
    order = setup_order_with_items
    refund_amount = process_refund(order.id)
    assert refund_amount == 10.0  # 2 items * $5.00 (price_at_purchase)
