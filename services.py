# Assuming the original code looked something like this, here's the corrected version:

def process_refund(order_id):
    order = Order.query.get(order_id)
    refund_amount = sum(order_item.quantity * order_item.price_at_purchase for order_item in order.order_items)
    # ... (rest of the refund processing logic remains the same)
    return refund_amount