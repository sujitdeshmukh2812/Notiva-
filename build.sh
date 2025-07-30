#!/bin/bash

echo "🚀 Building Notiva for Render deployment..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create database tables and admin user
echo "🗄️ Setting up database..."
python -c "
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create all tables
    db.create_all()
    print('✅ Database tables created')
    
    # Create admin user
    admin_email = 'sujitdeshmukh2812@gmail.com'
    existing_admin = User.query.filter_by(email=admin_email).first()
    
    if not existing_admin:
        admin_user = User(
            name='Sujit Deshmukh',
            email=admin_email,
            password_hash=generate_password_hash('Sujit@2812'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print('✅ Admin account created')
        print('Email: sujitdeshmukh2812@gmail.com')
        print('Password: Sujit@2812')
    else:
        print('✅ Admin account already exists')
"

echo "✅ Build completed successfully!"