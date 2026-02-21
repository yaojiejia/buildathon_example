def test_refund_amount_calculation():
    # Create a test order with a product
    order = Order(customer_id=1, status='pending', subtotal=100.0, total=100.0)
    order_item = OrderItem(order_id=order.id, product_id=1, quantity=2, price_at_purchase=50.0)
    db.add(order)
    db.add(order_item)
    db.commit()
    # Process a refund for the order
    refund_result = process_refund(db, order.id)
    # Verify the refund amount calculation
    assert refund_result['refund_amount'] == 100.0