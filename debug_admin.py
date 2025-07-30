#!/usr/bin/env python3
"""
Debug script to check admin account in database
Run this on Render to verify admin account exists
"""

import os
from app import app, db
from models import User
from werkzeug.security import check_password_hash

def debug_admin():
    with app.app_context():
        print("=== ADMIN ACCOUNT DEBUG ===")
        
        # Check if admin exists
        admin = User.query.filter_by(email='sujitdeshmukh2812@gmail.com').first()
        
        if admin:
            print("✅ Admin account found!")
            print(f"ID: {admin.id}")
            print(f"Name: {admin.name}")
            print(f"Email: {admin.email}")
            print(f"Is Admin: {admin.is_admin}")
            print(f"Password Hash Length: {len(admin.password_hash) if admin.password_hash else 'None'}")
            
            # Test password verification
            test_password = "Sujit@2812"
            if admin.password_hash:
                password_match = check_password_hash(admin.password_hash, test_password)
                print(f"Password Test: {'✅ PASS' if password_match else '❌ FAIL'}")
            else:
                print("❌ No password hash found!")
                
        else:
            print("❌ Admin account NOT found!")
            print("All users in database:")
            all_users = User.query.all()
            for user in all_users:
                print(f"  - {user.email} (Admin: {user.is_admin})")
        
        print(f"Total users: {User.query.count()}")

if __name__ == "__main__":
    debug_admin()