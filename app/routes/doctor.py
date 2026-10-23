from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from functools import wraps
import os
from app import db
from app.models import Appointment, Doctor, Patient, Document, Prescription
from app.forms import DoctorProfileForm
from app.utils import save_uploaded_file
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    doctor = current_user.doctor_profile
    today = datetime.utcnow().date()
    
    all_appts = Appointment.query.filter_by(doctor_id=doctor.id).all()
    
    todays_appts = [a for a in all_appts if a.date == today]
    pending_appts = [a for a in all_appts if a.status in ['Pending', 'Rescheduled']]
    completed_appts = [a for a in all_appts if a.status == 'Completed']
    
    recent_pending = Appointment.query.filter_by(doctor_id=doctor.id).filter(Appointment.status.in_(['Pending', 'Rescheduled'])).order_by(Appointment.date.asc()).limit(5).all()
    
    # Prepare data for Chart.js
    status_counts = {'Accepted': 0, 'Pending/Resched': 0, 'Completed': 0, 'Cancelled/Rej': 0}
    for a in all_appts:
        if a.status == 'Accepted': status_counts['Accepted'] += 1
        elif a.status in ['Pending', 'Rescheduled']: status_counts['Pending/Resched'] += 1
        elif a.status == 'Completed': status_counts['Completed'] += 1
        elif a.status in ['Cancelled', 'Rejected']: status_counts['Cancelled/Rej'] += 1
        
    chart_labels = list(status_counts.keys())
    chart_data = list(status_counts.values())
    
    return render_template('doctor/dashboard.html', 
                           today_count=len(todays_appts), 
                           pending_count=len(pending_appts),
                           completed_count=len(completed_appts),
                           recent_pending=recent_pending,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           current_date=today.strftime('%Y-%m-%d'))

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    appts = Appointment.query.filter_by(doctor_id=current_user.doctor_profile.id).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('doctor/appointments.html', appointments=appts)

@doctor_bp.route('/update_status/<int:appt_id>/<string:status>', methods=['POST'])
@login_required
@doctor_required
def update_status(appt_id, status):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.doctor_id != current_user.doctor_profile.id:
        flash('Unauthorized output action.', 'danger')
        return redirect(url_for('doctor.appointments'))
        
    valid_statuses = ['Accepted', 'Rejected', 'Completed']
    if status in valid_statuses:
        appt.status = status
        db.session.commit()
        flash(f'Appointment marked as {status}.', 'success')
    else:
        flash('Invalid status update.', 'danger')
        
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/reschedule_appointment/<int:appt_id>', methods=['POST'])
@login_required
@doctor_required
def reschedule_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.doctor_id != current_user.doctor_profile.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('doctor.appointments'))
        
    new_date_str = request.form.get('new_date')
    new_time_str = request.form.get('new_time')
    
    if new_date_str and new_time_str:
        try:
            appt.date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            appt.time = datetime.strptime(new_time_str, '%H:%M').time()
            appt.status = 'Rescheduled'
            db.session.commit()
            flash(f'Appointment rescheduled to {new_date_str} at {new_time_str}.', 'success')
        except ValueError:
            flash('Invalid date or time format provided.', 'danger')
    else:
        flash('Please provide both a new date and time.', 'danger')
        
    # Redirect to where they came from (dashboard or appointments page)
    # If the referrer contains 'dashboard', keep them there
    ref = request.referrer
    if ref and 'dashboard' in ref:
        return redirect(url_for('doctor.dashboard'))
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@doctor_required
def profile():
    doctor = current_user.doctor_profile
    form = DoctorProfileForm(
        specialization=doctor.specialization,
        experience=doctor.experience,
        availability=doctor.availability
    )
    if form.validate_on_submit():
        doctor.specialization = form.specialization.data
        doctor.experience = form.experience.data
        doctor.availability = form.availability.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))
        
    return render_template('doctor/profile.html', form=form)

@doctor_bp.route('/patient/<int:patient_id>/documents')
@login_required
@doctor_required
def patient_documents(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    docs = Document.query.filter_by(patient_id=patient.id).order_by(Document.upload_date.desc()).all()
    prescs = Prescription.query.filter_by(patient_id=patient.id).order_by(Prescription.created_at.desc()).all()
    
    return render_template('doctor/patient_documents.html', patient=patient, documents=docs, prescriptions=prescs)

@doctor_bp.route('/download_document/<int:doc_id>')
@login_required
@doctor_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    directory = os.path.dirname(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path))
    filename = os.path.basename(doc.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

@doctor_bp.route('/patient/<int:patient_id>/upload_prescription', methods=['POST'])
@login_required
@doctor_required
def upload_prescription(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if 'prescription' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('doctor.patient_documents', patient_id=patient.id))
        
    file = request.files['prescription']
    notes = request.form.get('notes', '')
    
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('doctor.patient_documents', patient_id=patient.id))
        
    if file:
        file_path = save_uploaded_file(file, subdir='prescriptions')
        if file_path:
            new_presc = Prescription(
                filename=file.filename,
                file_path=file_path,
                doctor_id=current_user.doctor_profile.id,
                patient_id=patient.id,
                notes=notes
            )
            db.session.add(new_presc)
            db.session.commit()
            flash('Prescription uploaded successfully!', 'success')
        else:
            flash('Invalid file type. Allowed types: PDF, PNG, JPG, JPEG', 'danger')
            
    return redirect(url_for('doctor.patient_documents', patient_id=patient.id))
