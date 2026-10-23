import sqlite3
import os

db_path = os.path.join('instance', 'hospital.db')

if os.path.exists(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add the profile_picture column
        cursor.execute('ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)')
        conn.commit()
        print("Successfully added profile_picture column to users table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column profile_picture already exists.")
        else:
            print(f"Error altering table: {e}")
            
    conn.close()
else:
    print(f"Database not found at {db_path}")
