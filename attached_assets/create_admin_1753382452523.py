#!/usr/bin/env python3
"""
Admin Account Creation Script for StudyGenie
This script creates a secure admin account with the specified credentials.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_admin_account():
    """Create admin account with secure credentials"""
    with app.app_context():
        # Admin credentials as specified
        admin_email = "sujitdeshmukh2812@gmail.com"
        admin_password = "Sujit@2812"
        admin_name = "Sujit Deshmukh"
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"Admin account with email {admin_email} already exists!")
            print(f"Current admin status: {existing_admin.is_admin}")
            
            # Update admin status if needed
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                db.session.commit()
                print("Updated existing user to admin status.")
            
            return existing_admin
        
        # Generate secure password hash
        password_hash = generate_password_hash(admin_password)
        
        # Create new admin user
        admin_user = User(
            name=admin_name,
            email=admin_email,
            password_hash=password_hash,
            is_admin=True
        )
        
        try:
            # Add to database
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Admin account created successfully!")
            print(f"Email: {admin_email}")
            print(f"Name: {admin_name}")
            print("Password: [SECURED - Use the provided password to login]")
            print("Admin Status: ✅ Enabled")
            print("\n🔐 Security Notes:")
            print("- Password has been hashed using Werkzeug security")
            print("- Original password is not stored in the database")
            print("- Admin can change password after first login")
            
            return admin_user
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin account: {e}")
            return None

def verify_admin_account():
    """Verify the admin account exists and can authenticate"""
    with app.app_context():
        admin_email = "sujitdeshmukh2812@gmail.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"\n✅ Admin Account Verification:")
            print(f"ID: {admin.id}")
            print(f"Name: {admin.name}")
            print(f"Email: {admin.email}")
            print(f"Admin Status: {'✅ Yes' if admin.is_admin else '❌ No'}")
            print(f"Created: {admin.created_at}")
            print(f"Password Hash: {admin.password_hash[:20]}...")
            return True
        else:
            print("❌ Admin account not found!")
            return False

if __name__ == "__main__":
    print("🚀 StudyGenie Admin Account Creation Script")
    print("=" * 50)
    
    # Create admin account
    admin = create_admin_account()
    
    if admin:
        print("\n" + "=" * 50)
        # Verify creation
        verify_admin_account()
        
        print("\n📝 Next Steps:")
        print("1. Start the StudyGenie application")
        print("2. Navigate to the login page")
        print("3. Use the admin credentials to login")
        print("4. Access admin features through the Admin dropdown")
        print("5. Consider changing the password after first login")
    else:
        print("\n❌ Failed to create admin account. Please check the error messages above.")
        sys.exit(1)