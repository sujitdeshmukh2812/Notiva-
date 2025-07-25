#!/usr/bin/env python3
"""
Admin Account Creation Script for Notiva
This script creates a secure admin account with the specified credentials.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Admin credentials
        admin_email = "sujitdeshmukh2812@gmail.com"
        admin_name = "Sujit Deshmukh"
        admin_password = "Sujit@2812"

        # Check if admin exists
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print("\n✨ Updating existing admin account...")
            # Update admin status and password
            admin.is_admin = True
            admin.name = admin_name
            admin.password_hash = generate_password_hash(admin_password)
            db.session.commit()
            print("✅ Admin account updated successfully!")
        else:
            print("\n✨ Creating new admin account...")
            # Create new admin
            admin = User(
                email=admin_email,
                name=admin_name,
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin account created successfully!")

        # Verify admin account
        print("\n🔍 Admin Account Details:")
        print(f"Name: {admin.name}")
        print(f"Email: {admin.email}")
        print(f"Admin Status: {'✅ Yes' if admin.is_admin else '❌ No'}")
        print(f"Password: {admin_password}")
        print("\n⚠️ Please save these credentials!")

if __name__ == "__main__":
    print("🚀 Notiva Admin Account Setup")
    print("=" * 50)
    create_admin()
    print("=" * 50)
    print("\n📝 Next Steps:")
    print("1. Go to /login")
    print("2. Use the admin email and password to log in")
    print("3. You should be redirected to the admin dashboard")
