#!/usr/bin/env python3
"""
Test admin login functionality
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

def test_admin_login():
    with app.app_context():
        print("=== TESTING ADMIN LOGIN ===")
        
        # Test password hashing and verification
        test_password = "Sujit@2812"
        test_hash = generate_password_hash(test_password)
        print(f"Test password: {test_password}")
        print(f"Generated hash: {test_hash[:50]}...")
        print(f"Hash verification: {check_password_hash(test_hash, test_password)}")
        
        # Check existing admin
        admin = User.query.filter_by(email='sujitdeshmukh2812@gmail.com').first()
        
        if admin:
            print(f"\n✅ Admin found in database")
            print(f"Email: {admin.email}")
            print(f"Name: {admin.name}")
            print(f"Is Admin: {admin.is_admin}")
            print(f"Password Hash: {admin.password_hash[:50]}...")
            
            # Test the check_password method
            password_check = admin.check_password(test_password)
            print(f"Admin.check_password('Sujit@2812'): {password_check}")
            
            # Test direct hash check
            direct_check = check_password_hash(admin.password_hash, test_password)
            print(f"Direct hash check: {direct_check}")
            
            if not password_check:
                print("\n🔧 FIXING PASSWORD...")
                admin.set_password(test_password)
                db.session.commit()
                print("Password updated, testing again...")
                print(f"New password check: {admin.check_password(test_password)}")
                
        else:
            print("❌ Admin not found, creating...")
            admin = User(
                name='Sujit Deshmukh',
                email='sujitdeshmukh2812@gmail.com',
                is_admin=True
            )
            admin.set_password(test_password)
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin created and password set")

if __name__ == "__main__":
    test_admin_login()