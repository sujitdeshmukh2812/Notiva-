from app import app, db
from models import User, Course, Year, Semester, Subject, Material, Rating, Bookmark, Notification, Doubt, Ad

def recreate_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables with new schema
        db.create_all()
        
        print("Database recreated successfully!")

if __name__ == "__main__":
    recreate_database() 