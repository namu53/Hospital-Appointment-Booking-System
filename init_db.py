from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # In case we aren't using Flask-Migrate for the very first initialization
    db.create_all()
    
    # Check if admin exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        import os
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
        print("Creating default admin user...")
        hashed_pw = generate_password_hash('admin123')
        admin_user = User(
            name='System Admin',
            email='admin@hospicare.com',
            password=hashed_pw,
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin@hospicare.com / admin123")
    else:
        print("Admin already exists.")
