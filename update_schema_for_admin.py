import os
import sqlite3
from app import create_app, db
from app.models import Admin
from werkzeug.security import generate_password_hash

app = create_app()

def update_schema_and_seed():
    with app.app_context():
        print("Creating new tables...")
        db.create_all()
        
        # Add column disease_id to prescriptions
        db_path = os.path.join(app.instance_path, 'hospital.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute('ALTER TABLE prescriptions ADD COLUMN disease_id INTEGER REFERENCES diseases(id)')
                conn.commit()
                print("Successfully added disease_id column to prescriptions table.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("Column disease_id already exists.")
                else:
                    print(f"Error altering prescriptions table: {e}")
            conn.close()
        else:
            print(f"Database not found at {db_path}")

        # Seed initial admin user
        admin_email = "admin@healthnest.com"
        existing_admin = Admin.query.filter_by(email=admin_email).first()
        if not existing_admin:
            print(f"Creating default admin account ({admin_email})...")
            hashed_pw = generate_password_hash("admin123")
            new_admin = Admin(
                name="Super Administrator",
                email=admin_email,
                password=hashed_pw,
                role="super_admin"
            )
            db.session.add(new_admin)
            db.session.commit()
            print("Admin account created successfully. Default password: 'admin123'")
        else:
            print("Default admin account already exists.")

if __name__ == '__main__':
    update_schema_and_seed()
