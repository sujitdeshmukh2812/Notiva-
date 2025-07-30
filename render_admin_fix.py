#!/usr/bin/env python3
"""
Emergency admin fix for Render deployment
Run this in Render console if admin login still fails
"""

from app import app, db
from models import User

def emergency_admin_fix():
    with app.app_context():
        print("🚨 EMERGENCY ADMIN FIX")
        
        # Find admin user
        admin = User.query.filter_by(email='sujitdeshmukh2812@gmail.com').first()
        
        if admin:
            print(f"Found admin: {admin.email}")
            print(f"Current admin status: {admin.is_admin}")
            
            # Force update password and admin status
            admin.set_password('Sujit@2812')
            admin.is_admin = True
            admin.name = 'Sujit Deshmukh'
            db.session.commit()
            
            print("✅ Admin password and status updated")
            
            # Test login
            test_result = admin.check_password('Sujit@2812')
            print(f"Password test: {'✅ PASS' if test_result else '❌ FAIL'}")
            
        else:
            print("❌ Admin not found - creating new admin")
            new_admin = User(
                name='Sujit Deshmukh',
                email='sujitdeshmukh2812@gmail.com',
                is_admin=True
            )
            new_admin.set_password('Sujit@2812')
            db.session.add(new_admin)
            db.session.commit()
            print("✅ New admin created")
        
        print("\n🎯 Login credentials:")
        print("Email: sujitdeshmukh2812@gmail.com")
        print("Password: Sujit@2812")

if __name__ == "__main__":
    emergency_admin_fix()