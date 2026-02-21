from sqlalchemy.orm import Session
from models import Product, Customer, Order, OrderItem, PromoCode

# patched by integration test
def process_refund(db: Session, order_id: int) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError('Order not found')
    if order.status == 'refunded':
        raise ValueError('Order already refunded')

    refund_amount = 0.0
    for item in order.items:
        refund_amount += item.price_at_purchase * item.quantity
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity

    customer = order.customer
    customer.loyalty_points = max(0, customer.loyalty_points - int(refund_amount))
    order.status = 'refunded'
    order.refund_amount = round(refund_amount, 2)
    db.commit()
    return {'order_id': order.id, 'refund_amount': round(refund_amount, 2), 'status': 'refunded'}
