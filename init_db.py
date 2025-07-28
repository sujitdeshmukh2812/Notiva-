import os
from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

# Use the production config by default for the init script
app = create_app(os.getenv('FLASK_CONFIG') or 'production')

def initialize_database():
    with app.app_context():
        print("Initializing database...")
        # Create all tables if they don't exist
        db.create_all()
        print("Database tables checked/created.")

        # Create admin user if it doesn't exist
        admin_email = os.environ.get('ADMIN_EMAIL', "sujitdeshmukh2812@gmail.com")
        admin_password = os.environ.get('ADMIN_PASSWORD', "Sujit@2812")

        if not User.query.filter_by(email=admin_email).first():
            print(f"Creating admin user: {admin_email}")
            admin = User(
                name="Sujit Deshmukh",
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

        print("Database initialization complete!")

if __name__ == "__main__":
    initialize_database()
