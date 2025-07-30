#!/usr/bin/env python3
"""
Script to check admin account status on Render deployment
Add this to your Render console to debug admin login issues
"""

import os
from app import app, db
from models import User
from werkzeug.security import check_password_hash

def check_render_admin():
    with app.app_context():
        print("=== RENDER ADMIN DEBUG ===")
        print(f"Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
        print(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
        
        # Check all users
        all_users = User.query.all()
        print(f"\nTotal users in database: {len(all_users)}")
        
        for user in all_users:
            print(f"- {user.email} (Admin: {user.is_admin}, ID: {user.id})")
        
        # Specifically check admin
        admin_email = 'sujitdeshmukh2812@gmail.com'
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"\n✅ Admin account found:")
            print(f"  Email: {admin.email}")
            print(f"  Name: {admin.name}")
            print(f"  Is Admin: {admin.is_admin}")
            print(f"  Password Hash: {'Set' if admin.password_hash else 'NOT SET'}")
            
            # Test password
            test_password = "Sujit@2812"
            if admin.password_hash:
                works = admin.check_password(test_password)
                print(f"  Password Test: {'✅ PASS' if works else '❌ FAIL'}")
                
                if not works:
                    print("\n🔧 FIXING PASSWORD...")
                    admin.set_password(test_password)
                    db.session.commit()
                    print("✅ Password updated and saved")
                    
                    # Test again
                    retest = admin.check_password(test_password)
                    print(f"  Retest: {'✅ PASS' if retest else '❌ STILL FAIL'}")
            else:
                print("❌ No password hash - setting password...")
                admin.set_password(test_password)
                db.session.commit()
                print("✅ Password set")
                
        else:
            print(f"\n❌ Admin account NOT found!")
            print("Creating admin account...")
            
            admin = User(
                name='Sujit Deshmukh',
                email=admin_email,
                is_admin=True
            )
            admin.set_password("Sujit@2812")
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin account created")

if __name__ == "__main__":
    check_render_admin()