import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Setup logging
    if not app.debug and not app.testing:
        if app.config.get('LOG_TO_STDOUT'):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/notiva.log',
                                             maxBytes=10240,
                                             backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Notiva startup')
    
    return app

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Import routes after app is created to avoid circular imports
from routes import *
