# Hospital Appointment Booking System

## Overview
A comprehensive Hospital Appointment Booking System with Clean Architecture in Python using Flask.

## Features
- **Admin Dashboard**: Analytics, approval mechanism for new doctors, manage all users.
- **Doctor Dashboard**: Manage profile details, availability schedule, accept/reject/complete appointments.
- **Patient Dashboard**: Find doctors by specialization, conflict-free appointment booking.

## Prerequisites
- Python 3.8+
- SQLite (Built-in, configured out-of-the-box)

## Folder Architecture
- `app/`: Contains the main application package.
  - `models.py`: SQLAlchemy Database schema.
  - `forms.py`: Flask-WTF Forms for input validation.
  - `routes/`: Blueprint modules separating auth, admin, doctor, and patient logic.
  - `templates/`: Jinja2 templates extending a base UI.
- `config.py`: Environment configurations.
- `run.py`: The application entry point.

## Step-by-Step Setup Guide

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Activate the Virtual Environment**
   *On Windows:*
   ```bash
   .\venv\Scripts\activate
   ```
   *On macOS/Linux:*
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database and Create Admin**
   The application uses `init_db.py` to auto-generate SQLite tables and create the default admin user.
   ```bash
   python init_db.py
   ```
   *Note: If you want pre-filled patient and doctor profiles, you can run:*
   ```bash
   python insert_mock_data.py
   ```

5. **Run the Application**
   ```bash
   python run.py
   ```
   *The server should now be running locally at `http://127.0.0.1:5000/`*

## Sample Accounts
After running `init_db.py` and `insert_mock_data.py` you can log in with the following valid credentials:
- **Admin**: `admin@hospicare.com` / `admin123`
- **Doctor**: `sarah@hospicare.com` / `doctor123`
- **Patient**: `emma@email.com` / `patient123`
