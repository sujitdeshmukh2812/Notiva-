#!/bin/bash

echo "🚀 Building Notiva for Render deployment..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create database tables and admin user
echo "🗄️ Setting up database..."
python -c "
import sys
import traceback
from app import app, db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

try:
    with app.app_context():
        print('🔧 Setting up database connection...')
        
        # Create all tables
        db.create_all()
        print('✅ Database tables created')
        
        # Ensure admin user exists and works
        admin_email = 'sujitdeshmukh2812@gmail.com'
        admin_password = 'Sujit@2812'
        
        # Check if admin exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            print('👤 Admin account found - updating password and admin status')
            existing_admin.set_password(admin_password)
            existing_admin.is_admin = True
            existing_admin.name = 'Sujit Deshmukh'
            db.session.commit()
            print('✅ Admin account updated successfully')
        else:
            print('👤 Creating new admin account...')
            admin_user = User(
                name='Sujit Deshmukh',
                email=admin_email,
                is_admin=True
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print('✅ Admin account created successfully')
        
        # Verify the admin account works
        print('🔍 Verifying admin login...')
        verify_admin = User.query.filter_by(email=admin_email).first()
        if verify_admin:
            password_works = verify_admin.check_password(admin_password)
            print(f'📧 Email: {admin_email}')
            print(f'🔑 Password: {admin_password}')
            print(f'👑 Is Admin: {verify_admin.is_admin}')
            print(f'✅ Login Test: {\"PASS\" if password_works else \"FAIL\"}')
            
            if password_works:
                print('🎉 Admin setup completed successfully!')
            else:
                print('❌ Password verification failed!')
                sys.exit(1)
        else:
            print('❌ Admin verification failed - user not found!')
            sys.exit(1)

except Exception as e:
    print(f'❌ Database setup failed: {e}')
    traceback.print_exc()
    sys.exit(1)
"

echo "✅ Build completed successfully!"