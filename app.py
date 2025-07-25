import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Basic configurations
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    if os.environ.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    else:
        # SQLite configuration - use absolute path
        base_dir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'instance', 'notiva.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # File upload configurations
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.environ.get('DATABASE_URL'):  # Only for SQLite
        os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Set up logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/notiva.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Notiva startup')
    
    return app

app = create_app()

# User loader function
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

from routes import *  # Import routes before database creation

# Initialize database and create admin user
with app.app_context():
    db.create_all()
    app.logger.info('Database tables created')
    
    # Create admin user if it doesn't exist
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin_email = "sujitdeshmukh2812@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name="Sujit Deshmukh",
            email=admin_email,
            password_hash=generate_password_hash("Sujit@2812"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info('Admin user created')
