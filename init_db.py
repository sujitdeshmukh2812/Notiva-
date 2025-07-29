#!/usr/bin/env python3
"""
Database Initialization Script for Notiva
This script initializes the database with required tables and sample data.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Course, Year, Semester, Subject

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("🔧 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create admin user if it doesn't exist
            admin_email = "sujitdeshmukh2812@gmail.com"
            admin = User.query.filter_by(email=admin_email).first()
            
            if not admin:
                print("👤 Creating admin user...")
                admin = User(
                    name="Sujit Deshmukh",
                    email=admin_email,
                    password_hash=generate_password_hash("Sujit@2812"),
                    is_admin=True
                )
                db.session.add(admin)
                print("✅ Admin user created!")
            else:
                print("👤 Admin user already exists!")
            
            # Create sample academic structure if it doesn't exist
            if Course.query.count() == 0:
                print("📚 Creating sample academic structure...")
                
                # Create sample courses
                cs_course = Course(name='B.Tech Computer Science')
                bba_course = Course(name='BBA')
                mba_course = Course(name='MBA')
                
                db.session.add_all([cs_course, bba_course, mba_course])
                db.session.flush()  # Get IDs without committing
                
                # Create years for CS course
                cs_year1 = Year(name='1st Year', course_id=cs_course.id)
                cs_year2 = Year(name='2nd Year', course_id=cs_course.id)
                cs_year3 = Year(name='3rd Year', course_id=cs_course.id)
                cs_year4 = Year(name='4th Year', course_id=cs_course.id)
                
                # Create years for BBA course
                bba_year1 = Year(name='1st Year', course_id=bba_course.id)
                bba_year2 = Year(name='2nd Year', course_id=bba_course.id)
                bba_year3 = Year(name='3rd Year', course_id=bba_course.id)
                
                db.session.add_all([cs_year1, cs_year2, cs_year3, cs_year4, bba_year1, bba_year2, bba_year3])
                db.session.flush()
                
                # Create semesters for CS 1st year
                cs_y1_sem1 = Semester(name='1st Semester', year_id=cs_year1.id)
                cs_y1_sem2 = Semester(name='2nd Semester', year_id=cs_year1.id)
                
                # Create semesters for CS 2nd year
                cs_y2_sem1 = Semester(name='1st Semester', year_id=cs_year2.id)
                cs_y2_sem2 = Semester(name='2nd Semester', year_id=cs_year2.id)
                
                db.session.add_all([cs_y1_sem1, cs_y1_sem2, cs_y2_sem1, cs_y2_sem2])
                db.session.flush()
                
                # Create subjects for CS 1st year 1st semester
                subjects = [
                    Subject(name='Mathematics I', semester_id=cs_y1_sem1.id),
                    Subject(name='Physics', semester_id=cs_y1_sem1.id),
                    Subject(name='Programming Fundamentals', semester_id=cs_y1_sem1.id),
                    Subject(name='English Communication', semester_id=cs_y1_sem1.id),
                ]
                
                # Create subjects for CS 1st year 2nd semester
                subjects.extend([
                    Subject(name='Mathematics II', semester_id=cs_y1_sem2.id),
                    Subject(name='Chemistry', semester_id=cs_y1_sem2.id),
                    Subject(name='Data Structures', semester_id=cs_y1_sem2.id),
                    Subject(name='Digital Logic', semester_id=cs_y1_sem2.id),
                ])
                
                # Create subjects for CS 2nd year 1st semester
                subjects.extend([
                    Subject(name='Operating Systems', semester_id=cs_y2_sem1.id),
                    Subject(name='Database Management', semester_id=cs_y2_sem1.id),
                    Subject(name='Object Oriented Programming', semester_id=cs_y2_sem1.id),
                    Subject(name='Computer Networks', semester_id=cs_y2_sem1.id),
                ])
                
                db.session.add_all(subjects)
                print("✅ Sample academic structure created!")
            else:
                print("📚 Academic structure already exists!")
            
            # Commit all changes
            db.session.commit()
            print("\n🎉 Database initialization completed successfully!")
            
            # Print summary
            print("\n📊 Database Summary:")
            print(f"Users: {User.query.count()}")
            print(f"Courses: {Course.query.count()}")
            print(f"Years: {Year.query.count()}")
            print(f"Semesters: {Semester.query.count()}")
            print(f"Subjects: {Subject.query.count()}")
            
            print("\n🔐 Admin Credentials:")
            print(f"Email: {admin_email}")
            print("Password: Sujit@2812")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    print("🚀 Notiva Database Initialization")
    print("=" * 50)
    
    if init_database():
        print("\n✅ Database initialization successful!")
        print("You can now start the application.")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)