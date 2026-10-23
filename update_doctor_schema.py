import os
import sqlite3
from app import create_app

app = create_app()

def update_doctor_schema():
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'hospital.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            columns_to_add = [
                ("age", "INTEGER"),
                ("gender", "VARCHAR(20)"),
                ("phone", "VARCHAR(20)"),
                ("address", "TEXT"),
                ("blood_group", "VARCHAR(10)"),
                ("date_of_birth", "DATE")
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute(f'ALTER TABLE doctors ADD COLUMN {col_name} {col_type}')
                    print(f"Successfully added {col_name} column to doctors table.")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"Column {col_name} already exists.")
                    else:
                        print(f"Error altering doctors table for {col_name}: {e}")
                        
            conn.commit()
            conn.close()
            print("Doctor schema update complete.")
        else:
            print(f"Database not found at {db_path}")

if __name__ == '__main__':
    update_doctor_schema()
