from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

# Initialize extensions (without the app object yet)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Set up where Flask-Login should redirect users who are not logged in
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    """
    Application Factory Function.
    This creates and configures the Flask application.
    It's modular and allows for easy testing with different configurations.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import and register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.doctor import doctor_bp
    from app.routes.patient import patient_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')

    return app
