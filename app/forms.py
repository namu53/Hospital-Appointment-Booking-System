from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Register as', choices=[('patient', 'Patient'), ('doctor', 'Doctor')], validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])
    experience = IntegerField('Experience (Years)', validators=[Optional(), NumberRange(min=0, max=100)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class BookingForm(FlaskForm):
    date = DateField('Appointment Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Appointment Time', validators=[DataRequired()])
    submit = SubmitField('Book Appointment')

class DoctorProfileForm(FlaskForm):
    specialization = StringField('Specialization', validators=[DataRequired()])
    experience = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=100)])
    availability = TextAreaField('Availability Schedule', validators=[Optional()]) # Used string description for simplicity
    submit = SubmitField('Update Profile')

class PatientProfileForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=150)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    contact = StringField('Contact Number', validators=[DataRequired()])
    submit = SubmitField('Update Profile')
