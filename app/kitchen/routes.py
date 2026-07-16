from flask import render_template, request, redirect, url_for, flash
from app.kitchen import bp
from app.models import Order
from app.extensions import db
from flask_login import login_required, current_user
from functools import wraps

def kitchen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'kitchen':
            flash('Access denied. Kitchen staff only.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@kitchen_required
def index():
    # Get active orders (Pending, Preparing, and recently Served)
    orders = Order.query.filter(Order.status.in_(['Pending', 'Preparing', 'Served'])).order_by(Order.created_at.desc()).limit(20).all()
    return render_template('kitchen/index.html', orders=orders)

@bp.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
@kitchen_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['Preparing', 'Served']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} is now {new_status}', 'success')
        
    return redirect(url_for('kitchen.index'))
