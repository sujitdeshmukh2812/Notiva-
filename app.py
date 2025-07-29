import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_migrate import Migrate

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production-12345")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_reset_on_return": "commit",
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10,
        "application_name": "notiva_app"
    }
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File Upload Configuration
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config["ALLOWED_EXTENSIONS"] = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'zip'}

# OpenAI Configuration
app.config["OPENAI_API_KEY"] = os.environ.get('OPENAI_API_KEY')

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)

# Login manager configuration will be set after blueprint registration

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.get(user_id)

    # Register routes
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Login manager configuration (after blueprint registration)
    login_manager.login_view = 'main.login'  # type: ignore
    login_manager.login_message = 'Please log in to access this page.'

    db.create_all()
    app.logger.info('Notiva startup - Database tables created successfully')