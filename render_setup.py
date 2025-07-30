#!/usr/bin/env python3
"""
Render Deployment Setup Script for Notiva
Run this script after deploying to Render to create the admin account.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def setup_render_deployment():
    with app.app_context():
        print("🚀 Setting up Notiva for Render deployment...")
        
        # Create all database tables
        db.create_all()
        print("✅ Database tables created")
        
        # Admin credentials
        admin_email = "sujitdeshmukh2812@gmail.com"
        admin_name = "Sujit Deshmukh"
        admin_password = "Sujit@2812"
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            print("✅ Admin account already exists")
            # Update password to ensure it's correct
            existing_admin.password_hash = generate_password_hash(admin_password)
            existing_admin.is_admin = True
            db.session.commit()
            print("✅ Admin password updated")
        else:
            # Create new admin account
            admin_user = User(
                name=admin_name,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin account created successfully")
        
        print("\n🔐 Admin Login Credentials:")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("\n✨ Your Notiva platform is ready on Render!")

if __name__ == "__main__":
    setup_render_deployment()