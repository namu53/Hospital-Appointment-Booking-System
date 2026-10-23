from app import create_app, db
from app.models import User, Doctor, Patient, Appointment
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Helper to hash passwords
    def hash_pw(pw):
        return generate_password_hash(pw)

    print("Adding sample doctors...")
    d1 = User(name="Sarah Jenkins", email="sarah@hospicare.com", password=hash_pw("doctor123"), role="doctor")
    d2 = User(name="Mark Lee", email="mark@hospicare.com", password=hash_pw("doctor123"), role="doctor")
    
    db.session.add_all([d1, d2])
    db.session.commit()
    
    doc1 = Doctor(user_id=d1.id, specialization="Cardiology", experience=15, availability="Mon-Fri 09:00-17:00", approved=True)
    doc2 = Doctor(user_id=d2.id, specialization="Neurology", experience=10, availability="Tue-Sat 10:00-18:00", approved=True)
    
    db.session.add_all([doc1, doc2])
    db.session.commit()
    
    print("Adding sample patients...")
    p1 = User(name="Emma Frost", email="emma@email.com", password=hash_pw("patient123"), role="patient")
    p2 = User(name="Bruce Wayne", email="bruce@email.com", password=hash_pw("patient123"), role="patient")
    
    db.session.add_all([p1, p2])
    db.session.commit()
    
    pat1 = Patient(user_id=p1.id, age=30, gender="Female", contact="555-0101")
    pat2 = Patient(user_id=p2.id, age=40, gender="Male", contact="555-0202")
    
    db.session.add_all([pat1, pat2])
    db.session.commit()
    
    print("Adding sample appointments...")
    today = datetime.utcnow().date()
    
    a1 = Appointment(doctor_id=doc1.id, patient_id=pat1.id, date=today + timedelta(days=1), time=datetime.strptime("10:00", "%H:%M").time(), status="Accepted")
    a2 = Appointment(doctor_id=doc2.id, patient_id=pat2.id, date=today + timedelta(days=2), time=datetime.strptime("14:30", "%H:%M").time(), status="Pending")
    
    db.session.add_all([a1, a2])
    db.session.commit()
    
    print("Sample data populated successfully!")
