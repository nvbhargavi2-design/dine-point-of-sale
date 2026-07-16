from flask import render_template, request, flash, redirect, url_for
from app.main import bp
from app.models import Category, Dish, Order
from flask_login import login_required, current_user
from app.extensions import db

@bp.route('/')
def index():
    categories = Category.query.all()
    dishes = Dish.query.filter_by(status=True).all()
    
    wishlist_dish_ids = []
    if current_user.is_authenticated and current_user.role == 'user':
        from app.models import Wishlist
        wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        wishlist_dish_ids = [item.dish_id for item in wishlist_items]
        
    return render_template('main/index.html', categories=categories, dishes=dishes, wishlist_dish_ids=wishlist_dish_ids)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if name and email:
            current_user.name = name
            current_user.email = email
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
            
    return render_template('main/profile.html')

@bp.route('/history')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('main/history.html', orders=orders)

from flask import jsonify
from app.models import Cart

@bp.route('/add_to_cart/<int:dish_id>', methods=['POST'])
@login_required
def add_to_cart(dish_id):
    if current_user.role != 'user':
        return jsonify({'success': False, 'message': 'Only users can add to cart'}), 403
        
    dish = Dish.query.get_or_404(dish_id)
    
    # Check if already in cart
    cart_item = Cart.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, dish_id=dish_id, quantity=1)
        db.session.add(cart_item)
        
    db.session.commit()
    
    # Get new cart total
    cart_count = sum(item.quantity for item in Cart.query.filter_by(user_id=current_user.id).all())
    
    return jsonify({'success': True, 'message': f'{dish.dish_name} added to cart', 'cart_count': cart_count})

@bp.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    subtotal = sum(item.dish.price * item.quantity for item in cart_items if item.dish)
    delivery_fee = 40.0 if subtotal > 0 and subtotal < 500 else 0.0
    taxes = subtotal * 0.05
    total = subtotal + delivery_fee + taxes
    
    return render_template('main/cart.html', cart_items=cart_items, subtotal=subtotal, delivery_fee=delivery_fee, taxes=taxes, total=total)

@bp.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False}), 403
        
    data = request.get_json()
    action = data.get('action')
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/cart/remove/<int:cart_id>', methods=['POST'])
@login_required
def remove_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('main.cart'))

import random

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('main.index'))
        
    subtotal = sum(item.dish.price * item.quantity for item in cart_items if item.dish)
    delivery_fee = 40.0 if subtotal < 500 else 0.0
    taxes = subtotal * 0.05
    total = subtotal + delivery_fee + taxes
    
    new_order = Order(
        user_id=current_user.id,
        table_no='Delivery',
        total_amount=total,
        status='Pending',
        payment_status='Pending'
    )
    db.session.add(new_order)
    db.session.flush() # To get order ID
    
    from app.models import OrderItem
    for item in cart_items:
        if item.dish:
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=item.dish_id,
                quantity=item.quantity,
                price=item.dish.price
            )
            db.session.add(order_item)
            db.session.delete(item) # Remove from cart
            
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('main.history'))

@bp.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
        
    if order.status != 'Pending':
        flash('Order cannot be cancelled as kitchen has already started preparing it.', 'danger')
        return redirect(url_for('main.history'))
        
    order.status = 'Cancelled'
    db.session.commit()
    
    flash('Your order has been cancelled successfully.', 'success')
    return redirect(url_for('main.history'))
@bp.route('/pay/<int:order_id>', methods=['GET', 'POST'])
@login_required
def pay_bill(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        return redirect(url_for('main.index'))
        
    if order.status != 'Served' or order.payment_status == 'Completed':
        flash('This order is not ready for payment or is already paid.', 'warning')
        return redirect(url_for('main.history'))
        
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # Simulate payment processing
        from app.models import Payment
        import uuid
        
        transaction_id = str(uuid.uuid4())[:10].upper()
        
        payment = Payment(
            order_id=order.id,
            payment_type=payment_method,
            transaction_id=transaction_id if payment_method != 'Cash' else None,
            amount=order.total_amount
        )
        
        order.payment_status = 'Completed'
        db.session.add(payment)
        db.session.commit()
        
        flash(f'Payment of ₹{order.total_amount} via {payment_method} successful!', 'success')
        return redirect(url_for('main.history'))
        
    return render_template('main/payment.html', order=order)

from app.models import Wishlist

@bp.route('/wishlist/toggle/<int:dish_id>', methods=['POST'])
@login_required
def toggle_wishlist(dish_id):
    if current_user.role != 'user':
        return jsonify({'success': False, 'message': 'Only users can use the wishlist.'}), 403
        
    dish = Dish.query.get_or_404(dish_id)
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, dish_id=dish.id).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        new_item = Wishlist(user_id=current_user.id, dish_id=dish.id)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})

@bp.route('/wishlist')
@login_required
def wishlist():
    if current_user.role != 'user':
        return redirect(url_for('main.index'))
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('main/wishlist.html', wishlist_items=wishlist_items)
