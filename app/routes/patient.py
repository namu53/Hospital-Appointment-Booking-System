from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Doctor, Patient, Appointment, Document, Prescription
from datetime import datetime
import os
from app.utils import save_uploaded_file

patient_bp = Blueprint('patient', __name__)

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    patient = current_user.patient_profile
    today = datetime.utcnow().date()
    all_appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    
    upcoming = [a for a in all_appointments if a.date >= today and a.status in ['Pending', 'Accepted']]
    past = [a for a in all_appointments if a.date < today or a.status in ['Completed', 'Cancelled', 'Rejected']]
    
    recent = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.desc(), Appointment.time.desc()).limit(5).all()
    
    # Prepare data for Chart.js
    status_counts = {'Accepted': 0, 'Pending': 0, 'Completed': 0, 'Cancelled/Rejected': 0}
    for a in all_appointments:
        if a.status == 'Accepted': status_counts['Accepted'] += 1
        elif a.status == 'Pending' or a.status == 'Rescheduled': status_counts['Pending'] += 1
        elif a.status == 'Completed': status_counts['Completed'] += 1
        elif a.status in ['Cancelled', 'Rejected']: status_counts['Cancelled/Rejected'] += 1
        
    chart_labels = list(status_counts.keys())
    chart_data = list(status_counts.values())
    
    return render_template('patient/dashboard.html', 
                           upcoming_count=len(upcoming), 
                           past_count=len(past), 
                           recent_appointments=recent,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@patient_bp.route('/find_doctors')
@login_required
@patient_required
def find_doctors():
    doctors = Doctor.query.filter_by(approved=True).all()
    return render_template('patient/find_doctors.html', doctors=doctors)

@patient_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        
        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Conflict Check
            existing = Appointment.query.filter_by(doctor_id=doctor.id, date=appt_date, time=appt_time).first()
            if existing and existing.status not in ['Cancelled', 'Rejected']:
                flash('This time slot is already booked. Please choose another.', 'warning')
                return redirect(url_for('patient.book_appointment', doctor_id=doctor.id))
            
            appointment = Appointment(
                doctor_id=doctor.id,
                patient_id=current_user.patient_profile.id,
                date=appt_date,
                time=appt_time,
                status='Pending'
            )
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment request sent successfully!', 'success')
            return redirect(url_for('patient.dashboard'))
            
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            
    return render_template('patient/book_appointment.html', doctor=doctor)

@patient_bp.route('/my_appointments')
@login_required
@patient_required
def my_appointments():
    appointments = Appointment.query.filter_by(patient_id=current_user.patient_profile.id).order_by(Appointment.date.desc()).all()
    return render_template('patient/my_appointments.html', appointments=appointments)

@patient_bp.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
@login_required
@patient_required
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != current_user.patient_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('patient.my_appointments'))
        
    if appt.status in ['Pending', 'Accepted']:
        appt.status = 'Cancelled'
        db.session.commit()
        flash('Appointment cancelled.', 'info')
    else:
        flash('Cannot cancel this appointment.', 'warning')
        
    return redirect(url_for('patient.my_appointments'))

@patient_bp.route('/documents', methods=['GET'])
@login_required
@patient_required
def documents():
    docs = Document.query.filter_by(patient_id=current_user.patient_profile.id).order_by(Document.upload_date.desc()).all()
    return render_template('patient/documents.html', documents=docs)

@patient_bp.route('/upload_document', methods=['POST'])
@login_required
@patient_required
def upload_document():
    if 'document' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('patient.documents'))
        
    file = request.files['document']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('patient.documents'))
        
    if file:
        file_path = save_uploaded_file(file, subdir='documents')
        if file_path:
            new_doc = Document(
                filename=file.filename,
                file_path=file_path,
                patient_id=current_user.patient_profile.id
            )
            db.session.add(new_doc)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
        else:
            flash('Invalid file type. Allowed types: PDF, PNG, JPG, JPEG', 'danger')
            
    return redirect(url_for('patient.documents'))

@patient_bp.route('/download_document/<int:doc_id>')
@login_required
@patient_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.patient_id != current_user.patient_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('patient.documents'))
        
    directory = os.path.dirname(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path))
    filename = os.path.basename(doc.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

@patient_bp.route('/delete_document/<int:doc_id>', methods=['POST'])
@login_required
@patient_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.patient_id != current_user.patient_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('patient.documents'))
        
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        flash('Error deleting file from disk.', 'warning')
        
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted successfully.', 'success')
    return redirect(url_for('patient.documents'))

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    prescs = Prescription.query.filter_by(patient_id=current_user.patient_profile.id).order_by(Prescription.created_at.desc()).all()
    return render_template('patient/prescriptions.html', prescriptions=prescs)

@patient_bp.route('/download_prescription/<int:presc_id>')
@login_required
@patient_required
def download_prescription(presc_id):
    presc = Prescription.query.get_or_404(presc_id)
    if presc.patient_id != current_user.patient_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('patient.prescriptions'))
        
    directory = os.path.dirname(os.path.join(current_app.config['UPLOAD_FOLDER'], presc.file_path))
    filename = os.path.basename(presc.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

@patient_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
@patient_required
def edit_profile():
    patient = current_user.patient_profile
    if request.method == 'POST':
        # Update User data
        current_user.name = request.form.get('name')
        
        # Update Patient data
        age_val = request.form.get('age')
        patient.age = int(age_val) if age_val and age_val.isdigit() else None
        
        patient.gender = request.form.get('gender')
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.blood_group = request.form.get('blood_group')
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        patient.emergency_contact = request.form.get('emergency_contact')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.edit_profile'))
        
    # Calculate Completion %
    fields = [current_user.name, patient.age, patient.gender, patient.phone, 
              patient.address, patient.blood_group, patient.date_of_birth, patient.emergency_contact]
    filled = sum(1 for f in fields if f)
    completion_percentage = int((filled / len(fields)) * 100)
    
    return render_template('patient/edit_profile.html', patient=patient, completion_percentage=completion_percentage)
