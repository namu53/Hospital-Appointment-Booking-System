import os

class Config:
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-123'
    
    # Database Configuration
    # We use SQLite for development, easily scalable to PostgreSQL by changing this URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hospital.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max limit
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
