from flask import render_template, redirect, url_for, flash, request
from app.auth import bp
from app.models import User
from app.extensions import db
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask import session

def generate_otp():
    """Mock OTP generation for testing without a real SMS gateway."""
    otp = str(random.randint(100000, 999999))
    print(f"\n{'='*40}\nMock SMS Sent! OTP is: {otp}\n{'='*40}\n")
    return otp

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        
        if not mobile or not email:
            flash('Mobile number and email are required.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Generate OTP and store in session
        otp = generate_otp()
        session['otp'] = otp
        session['auth_mobile'] = mobile
        session['auth_email'] = email
        
        flash('OTP sent to your mobile number!', 'success')
        flash(f'TEST MODE: Your OTP is {otp} (Since SMS API is not configured yet)', 'info')
        return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/register.html')

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if 'auth_mobile' not in session:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('auth.register'))
        
    if request.method == 'POST':
        entered_otp = str(request.form.get('otp', '')).strip()
        stored_otp = str(session.get('otp', '')).strip()
        
        if entered_otp and stored_otp and entered_otp == stored_otp:
            mobile = session.get('auth_mobile')
            email = session.get('auth_email')
            
            # Check if user exists
            user = User.query.filter_by(mobile=mobile).first()
            if not user:
                # Create new user with placeholder name and password
                user = User(
                    name="Guest",
                    mobile=mobile,
                    email=email,
                    password=generate_password_hash("NOPASSWORD"),
                    role='user',
                    is_verified=True
                )
                db.session.add(user)
                db.session.commit()
            
            # Auto login
            login_user(user)
            
            # Clear session
            session.pop('otp', None)
            session.pop('auth_mobile', None)
            session.pop('auth_email', None)
            
            flash('Successfully authenticated!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('auth/verify_otp.html', mobile=session.get('auth_mobile'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        user = User.query.filter_by(mobile=mobile).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            next_page = request.args.get('next')
            if not next_page or next_page.startswith('/auth/'):
                if user.role == 'admin':
                    next_page = url_for('admin.index')
                elif user.role == 'kitchen':
                    next_page = url_for('kitchen.index')
                else:
                    next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid username/mobile or password', 'danger')
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
