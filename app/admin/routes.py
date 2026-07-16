from flask import render_template, redirect, url_for, request, flash, current_app
from app.extensions import db
from werkzeug.utils import secure_filename
import os
from app.admin import bp
from app.models import Order, User, Dish, Category
from flask_login import login_required

@bp.route('/')
@login_required
def index():
    # Fetch 5 most recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/index.html', recent_orders=recent_orders)

@bp.route('/login')
def login():
    return redirect(url_for('auth.login', next=request.path))

@bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        if category_name:
            new_category = Category(category_name=category_name)
            db.session.add(new_category)
            db.session.commit()
            flash(f'Category "{category_name}" added successfully!', 'success')
            return redirect(url_for('admin.categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash(f'Category deleted successfully.', 'success')
    return redirect(url_for('admin.categories'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@bp.route('/dishes', methods=['GET', 'POST'])
@login_required
def dishes():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        dish_name = request.form.get('dish_name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Store relative URL for the browser
                image_url = url_for('static', filename=f'uploads/dishes/{filename}')
        
        if dish_name and price and category_id:
            new_dish = Dish(
                category_id=category_id,
                dish_name=dish_name,
                description=description,
                price=float(price),
                image=image_url
            )
            db.session.add(new_dish)
            db.session.commit()
            flash(f'Dish "{dish_name}" added successfully!', 'success')
            return redirect(url_for('admin.dishes'))
        else:
            flash('Please fill in all required fields.', 'danger')
            
    categories = Category.query.all()
    dishes = Dish.query.all()
    return render_template('admin/dishes.html', categories=categories, dishes=dishes)

@bp.route('/dishes/delete/<int:id>', methods=['POST'])
@login_required
def delete_dish(id):
    dish = Dish.query.get_or_404(id)
    db.session.delete(dish)
    db.session.commit()
    flash(f'Dish deleted successfully.', 'success')
    return redirect(url_for('admin.dishes'))

@bp.route('/dishes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_dish(id):
    dish = Dish.query.get_or_404(id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        dish_name = request.form.get('dish_name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        if dish_name and price and category_id:
            dish.category_id = category_id
            dish.dish_name = dish_name
            dish.description = description
            dish.price = float(price)
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    dish.image = url_for('static', filename=f'uploads/dishes/{filename}')
            
            db.session.commit()
            flash(f'Dish "{dish_name}" updated successfully!', 'success')
            return redirect(url_for('admin.dishes'))
        else:
            flash('Please fill in all required fields.', 'danger')
            
    return render_template('admin/edit_dish.html', dish=dish, categories=categories)

@bp.route('/orders')
@login_required
def orders():
    # Fetch all orders, ordered by newest first
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@bp.route('/users')
@login_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@bp.route('/order/view/<int:id>')
@login_required
def view_order(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/view_order.html', order=order)
