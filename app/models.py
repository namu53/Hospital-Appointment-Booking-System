from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# Load user callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('admin_'):
        return Admin.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('user_'):
        return User.query.get(int(user_id.split('_')[1]))
    else:
        # Fallback for old integer-based sessions
        return User.query.get(int(user_id))

class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='super_admin') # 'super_admin' or 'staff_admin'
    profile_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"admin_{self.id}"

class Disease(db.Model):
    __tablename__ = 'diseases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

patient_disease = db.Table('patient_disease',
    db.Column('patient_id', db.Integer, db.ForeignKey('patients.id'), primary_key=True),
    db.Column('disease_id', db.Integer, db.ForeignKey('diseases.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient') # 'admin', 'doctor', 'patient'
    profile_picture = db.Column(db.String(255), nullable=True)
    
    # Relationships
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade="all, delete-orphan")
    patient_profile = db.relationship('Patient', backref='user', uselist=False, cascade="all, delete-orphan")

    def get_id(self):
        return f"user_{self.id}"

    def __repr__(self):
        return f"<User {self.email}>"

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer, default=0)
    availability = db.Column(db.String(500), default='{}') # Can store JSON string of shifts
    approved = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    contact = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    documents = db.relationship('Document', backref='patient', lazy=True, cascade="all, delete-orphan")
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, cascade="all, delete-orphan")
    diseases = db.relationship('Disease', secondary=patient_disease, backref=db.backref('patients', lazy='dynamic'))

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Accepted, Rejected, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    disease = db.relationship('Disease', backref='prescriptions')
