from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from config import config
from models import db, User
from routes import auth_bp, patient_bp, admin_bp
from routes import patient_bp
import os


def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(admin_bp)
    
    # Create tables and sample data
    with app.app_context():
        db.create_all()
        create_sample_data()
    
    return app

def create_sample_data():
    """Create sample data if database is empty"""
    from werkzeug.security import generate_password_hash
    from models import User, Doctor, DoctorSchedule
    from datetime import time
    
    # Check if data already exists
    if User.query.first():
        return
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@hospital.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        phone='1234567890'
    )
    db.session.add(admin)
    
    # Create sample patient
    patient = User(
        username='patient_user',
        email='patient@hospital.com',
        password_hash=generate_password_hash('patient123'),
        role='patient',
        phone='0987654321'
    )
    db.session.add(patient)
    
    # Create sample doctors
    doctors_ = [
        {
            'name': 'Dr. John Smith',
            'specialization': 'Cardiology',
            'email': 'john.smith@hospital.com',
            'phone': '555-0101',
            'experience': 15,
            'qualifications': 'MD, FACC, Fellowship in Interventional Cardiology'
        },
        {
            'name': 'Dr. Sarah Johnson',
            'specialization': 'Dermatology',
            'email': 'sarah.johnson@hospital.com',
            'phone': '555-0102',
            'experience': 12,
            'qualifications': 'MD, Board Certified Dermatologist'
        },
        {
            'name': 'Dr. Michael Brown',
            'specialization': 'Orthopedics',
            'email': 'michael.brown@hospital.com',
            'phone': '555-0103',
            'experience': 18,
            'qualifications': 'MD, MS Orthopedics, Joint Replacement Specialist'
        },
        {
            'name': 'Dr. Emily Davis',
            'specialization': 'Pediatrics',
            'email': 'emily.davis@hospital.com',
            'phone': '555-0104',
            'experience': 10,
            'qualifications': 'MD, Board Certified Pediatrician'
        },
        {
            'name': 'Dr. Robert Wilson',
            'specialization': 'Neurology',
            'email': 'robert.wilson@hospital.com',
            'phone': '555-0105',
            'experience': 20,
            'qualifications': 'MD, PhD, Fellowship in Epilepsy'
        }
    ]
    
    for doctor_data in doctors_:
        doctor = Doctor(**doctor_data)
        db.session.add(doctor)
        db.session.flush()  # get doctor.id`
        
        # Create sample schedule (Monday to Friday, 9 AM to 5 PM)
        for day in range(5):  # Monday to Friday
            schedule = DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(17, 0),   # 5:00 PM
                slot_duration=30
            )
            db.session.add(schedule)
    
    db.session.commit()
    print("Sample data created successfully!")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
