import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///notiva.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

with app.app_context():
    # Import models and routes
    from models import User, Material, Course, Year, Semester, Subject, Ad
    from routes import *
    
    # Create all database tables
    db.create_all()
    
    # Create default academic structure if it doesn't exist
    if Course.query.count() == 0:
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
        db.session.commit()
        logging.info("Default academic structure created")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
