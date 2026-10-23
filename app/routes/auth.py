from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, session
from flask_login import login_user, logout_user, current_user, login_required
import json
import os
from app import db
from app.models import User, Doctor, Patient, Appointment, Admin
from app.forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import save_uploaded_file
from werkzeug.utils import secure_filename
import uuid
from PIL import Image

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))
    return render_template('index.html')

from sqlalchemy.exc import IntegrityError

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user_exists = User.query.filter_by(email=form.email.data).first()
        if user_exists:
            flash('Email already registered! Please login.', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = generate_password_hash(form.password.data)
        user = User(name=form.name.data, email=form.email.data, password=hashed_password, role=form.role.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create corresponding profile
            if user.role == 'doctor':
                doc_spec = form.specialization.data if form.specialization.data else 'General'
                doc_exp = form.experience.data if form.experience.data is not None else 0
                # Auto-approve doctors so they appear immediately
                doctor = Doctor(user_id=user.id, specialization=doc_spec, experience=doc_exp, approved=True)
                db.session.add(doctor)
            elif user.role == 'patient':
                patient = Patient(user_id=user.id)
                db.session.add(patient)
                
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # First check if the user is an Admin
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and check_password_hash(admin.password, form.password.data):
            login_user(admin, remember=form.remember.data)
            session['user_id'] = admin.id
            session['role'] = 'admin'
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
            
        # Then check Patient and Doctor separately (handled by unified User model)
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            session['user_id'] = user.id
            session['role'] = user.role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
                
            # Role-based dashboard redirect
            if user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
            else:
                return redirect(url_for('auth.index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.index'))

@auth_bp.route('/about')
def about():
    return render_template('about.html')

@auth_bp.route('/contact')
def contact():
    return render_template('contact.html')

@auth_bp.route('/analytics')
def analytics():
    # Generate realistic healthcare mock data for the dashboard
    import random
    from datetime import datetime, timedelta
    
    # 1. Disease Distribution (Doughnut Chart)
    disease_labels = ['Hypertension', 'Type 2 Diabetes', 'Asthma', 'Seasonal Flu', 'Heart Disease', 'Arthritis']
    # Use weights for realistic distribution
    disease_data = [random.randint(250, 400), random.randint(180, 300), random.randint(100, 200), random.randint(150, 350), random.randint(80, 150), random.randint(120, 250)]
    
    # 2. Patient Demographics by Age (Polar Area Chart)
    age_labels = ['0-18 Years', '19-35 Years', '36-50 Years', '51-65 Years', '65+ Years']
    age_data = [random.randint(100, 200), random.randint(300, 500), random.randint(400, 600), random.randint(500, 700), random.randint(600, 900)]
    
    # 3. Monthly Admissions vs Discharges (Line/Bar Chart)
    # Generate last 6 months
    monthly_labels = []
    admissions_data = []
    discharges_data = []
    
    today = datetime.now()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        monthly_labels.append(month_date.strftime('%b'))
        
        base_admissions = random.randint(400, 800)
        # Discharges generally closely follow admissions but slightly lower to account for inpatient growth
        base_discharges = int(base_admissions * random.uniform(0.85, 0.95))
        
        admissions_data.append(base_admissions)
        discharges_data.append(base_discharges)
        
    return render_template('analytics.html',
                           disease_labels=disease_labels,
                           disease_data=disease_data,
                           age_labels=age_labels,
                           age_data=age_data,
                           monthly_labels=monthly_labels,
                           admissions_data=admissions_data,
                           discharges_data=discharges_data)

@auth_bp.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        flash('No file provided.', 'danger')
        return redirect(request.referrer or url_for('auth.index'))
        
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file.', 'warning')
        return redirect(request.referrer or url_for('auth.index'))
        
    if file:
        file_path = save_uploaded_file(file, subdir='profiles')
        if file_path:
            current_user.profile_picture = file_path
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Invalid file type. Allowed types: PNG, JPG, JPEG.', 'danger')
            
    return redirect(request.referrer or url_for('auth.index'))

@auth_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@auth_bp.route('/upload-profile', methods=['POST'])
@login_required
def upload_profile():
    if 'profile_image' not in request.files:
        flash('No file provided.', 'danger')
        return redirect(request.referrer or url_for('auth.index'))
        
    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file.', 'warning')
        return redirect(request.referrer or url_for('auth.index'))
        
    if file:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ['jpg', 'jpeg', 'png']:
            flash('Invalid file type. Allowed types: PNG, JPG, JPEG.', 'danger')
            return redirect(request.referrer or url_for('auth.index'))
            
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        target_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile')
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, unique_filename)
        
        # Save and resize using Pillow
        try:
            image = Image.open(file)
            image = image.convert('RGB')
            image = image.resize((300, 300), Image.Resampling.LANCZOS)
            image.save(file_path, quality=90)
            
            relative_path = f"uploads/profile/{unique_filename}"
            
            # Update the respective model
            if current_user.role == 'doctor':
                current_user.doctor_profile.profile_image = relative_path
            elif current_user.role == 'patient':
                current_user.patient_profile.profile_image = relative_path
            db.session.commit()
            
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return {"status": "success", "message": "Profile picture updated successfully!"}, 200
                
            flash('Profile picture updated successfully!', 'success')
            
        except Exception as e:
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return {"status": "error", "message": str(e)}, 400
            flash(f'Error processing image: {str(e)}', 'danger')

    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return {"status": "error", "message": "Invalid file type"}, 400
    
    return redirect(request.referrer or url_for('auth.index'))

@auth_bp.route('/get-profile', methods=['GET'])
@login_required
def get_profile():
    if current_user.role == 'doctor' and getattr(current_user, 'doctor_profile', None) and current_user.doctor_profile.profile_image:
        return redirect(url_for('static', filename=current_user.doctor_profile.profile_image))
    elif current_user.role == 'patient' and getattr(current_user, 'patient_profile', None) and current_user.patient_profile.profile_image:
        return redirect(url_for('static', filename=current_user.patient_profile.profile_image))
    return redirect("https://ui-avatars.com/api/?name=" + current_user.name + "&background=f5b942&color=fff&size=200")


