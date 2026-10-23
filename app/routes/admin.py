from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app import db
from app.models import Admin, User, Doctor, Patient, Appointment, Disease, Document, Prescription
from werkzeug.security import check_password_hash
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'admin':
            flash('Access Denied: You must be an administrator to view this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin, remember=remember)
            session['user_id'] = admin.id
            session['role'] = 'admin'
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash('Admin login unsuccessful. Please check credentials.', 'danger')

    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Admin successfully logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    total_docs = Document.query.count() + Prescription.query.count()
    
    # Status Distribution
    status_counts = db.session.query(Appointment.status, db.func.count(Appointment.id)).group_by(Appointment.status).all()
    status_labels = [s[0] for s in status_counts]
    status_data = [s[1] for s in status_counts]
    
    # Disease distribution
    # We count how many patients are linked to each disease
    disease_counts = db.session.query(Disease.name, db.func.count(Patient.id)).join(Disease.patients).group_by(Disease.name).all()
    disease_labels = [d[0] for d in disease_counts]
    disease_data = [d[1] for d in disease_counts]
    
    # Appointments over time
    date_counts = db.session.query(Appointment.date, db.func.count(Appointment.id)).group_by(Appointment.date).order_by(Appointment.date).limit(10).all()
    date_labels = [d[0].strftime('%Y-%m-%d') if hasattr(d[0], 'strftime') else d[0] for d in date_counts]
    date_data = [d[1] for d in date_counts]

    return render_template('admin/dashboard.html',
                           patients_count=total_patients,
                           doctors_count=total_doctors,
                           appointments_count=total_appointments,
                           docs_count=total_docs,
                           status_labels=json.dumps(status_labels),
                           status_data=json.dumps(status_data),
                           disease_labels=json.dumps(disease_labels),
                           disease_data=json.dumps(disease_data),
                           date_labels=json.dumps(date_labels),
                           date_data=json.dumps(date_data))

# --- Patient Management ---
@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    patients = Patient.query.all()
    return render_template('admin/patients.html', patients=patients)

@admin_bp.route('/patient/details/<int:patient_id>')
@login_required
@admin_required
def patient_details(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('admin/patient_details.html', patient=patient)

@admin_bp.route('/patient/delete/<int:patient_id>', methods=['POST'])
@login_required
@admin_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    user = patient.user
    db.session.delete(patient)
    db.session.delete(user) # Hard delete the backing user too
    db.session.commit()
    flash('Patient deleted successfully.', 'success')
    return redirect(url_for('admin.patients'))

# --- Doctor Management ---
@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    doctors = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=doctors)

@admin_bp.route('/doctor/approve/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def approve_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.approved = not doctor.approved # Toggle approval
    db.session.commit()
    flash(f'Doctor activation status changed to {doctor.approved}.', 'success')
    return redirect(url_for('admin.doctors'))

@admin_bp.route('/doctor/delete/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = doctor.user
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()
    flash('Doctor deleted successfully.', 'success')
    return redirect(url_for('admin.doctors'))

# --- Appointment Management ---
@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    appointments = Appointment.query.all()
    return render_template('admin/appointments.html', appointments=appointments)

@admin_bp.route('/appointment/delete/<int:app_id>', methods=['POST'])
@login_required
@admin_required
def delete_appointment(app_id):
    app = Appointment.query.get_or_404(app_id)
    db.session.delete(app)
    db.session.commit()
    flash('Appointment deleted successfully.', 'success')
    return redirect(url_for('admin.appointments'))

# --- Disease Management ---
@admin_bp.route('/diseases', methods=['GET', 'POST'])
@login_required
@admin_required
def diseases():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        symptoms = request.form.get('symptoms')
        
        if Disease.query.filter_by(name=name).first():
            flash('Processing error: Disease already exists.', 'danger')
        else:
            new_disease = Disease(name=name, description=description, symptoms=symptoms)
            db.session.add(new_disease)
            db.session.commit()
            flash('Disease added successfully.', 'success')
            return redirect(url_for('admin.diseases'))
            
    all_diseases = Disease.query.all()
    return render_template('admin/diseases.html', diseases=all_diseases)

@admin_bp.route('/disease/delete/<int:disease_id>', methods=['POST'])
@login_required
@admin_required
def delete_disease(disease_id):
    disease = Disease.query.get_or_404(disease_id)
    db.session.delete(disease)
    db.session.commit()
    flash('Disease removed.', 'success')
    return redirect(url_for('admin.diseases'))

# --- File Management ---
@admin_bp.route('/files')
@login_required
@admin_required
def files():
    documents = Document.query.all()
    prescriptions = Prescription.query.all()
    return render_template('admin/files.html', documents=documents, prescriptions=prescriptions)

@admin_bp.route('/file/delete/doc/<int:doc_id>', methods=['POST'])
@login_required
@admin_required
def delete_doc(doc_id):
    doc = Document.query.get_or_404(doc_id)
    db.session.delete(doc)
    db.session.commit()
    flash('Document record deleted.', 'success')
    return redirect(url_for('admin.files'))

@admin_bp.route('/file/delete/presc/<int:presc_id>', methods=['POST'])
@login_required
@admin_required
def delete_presc(presc_id):
    presc = Prescription.query.get_or_404(presc_id)
    db.session.delete(presc)
    db.session.commit()
    flash('Prescription record deleted.', 'success')
    return redirect(url_for('admin.files'))
