import pymysql
from config import Config
from app import create_app
from app.extensions import db
from app.models import User, Category, Dish, Table, Cart, Order, OrderItem, Payment
from werkzeug.security import generate_password_hash

def init_db():
    # Connect to MySQL server to create the database if it doesn't exist
    print("Connecting to MySQL...")
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASS
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
        connection.commit()
        connection.close()
        print(f"Database {Config.DB_NAME} ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    # Create tables
    app = create_app()
    with app.app_context():
        db.create_all()
        print("All tables created successfully.")
        
        # Create default Admin and Kitchen users if they don't exist
        if not User.query.filter_by(mobile='admin').first():
            admin_user = User(
                name='Admin',
                mobile='admin',
                email='admin@dinepos.com',
                password=generate_password_hash('admin123'),
                is_verified=True,
                role='admin'
            )
            db.session.add(admin_user)
            
        if not User.query.filter_by(mobile='kitchen').first():
            kitchen_user = User(
                name='Kitchen Manager',
                mobile='kitchen',
                email='kitchen@dinepos.com',
                password=generate_password_hash('kitchen123'),
                is_verified=True,
                role='kitchen'
            )
            db.session.add(kitchen_user)
            
        db.session.commit()
        print("Default users created.")

if __name__ == '__main__':
    init_db()
