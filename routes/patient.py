# routes/patient.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Doctor, Appointment, DoctorSchedule, db
from datetime import datetime, timedelta

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.id,
        status='scheduled'
    ).filter(Appointment.appointment_date >= datetime.now().date()).all()
    
    return render_template('patient_dashboard.html', 
                         appointments=upcoming_appointments)

@patient_bp.route('/doctors')
@login_required
def view_doctors():
    doctors = Doctor.query.filter_by(is_available=True).all()
    return render_template('doctors.html', doctors=doctors)

@patient_bp.route('/book/<int:doctor_id>')
@login_required
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get available slots for next 30 days
    available_slots = get_available_slots(doctor_id, days=30)
    
    return render_template('book_appointment.html', 
                         doctor=doctor, 
                         slots=available_slots)

def get_available_slots(doctor_id, days=30):
    """Generate available time slots for a doctor"""
    doctor = Doctor.query.get(doctor_id)
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id).all()
    
    available_slots = []
    today = datetime.now().date()
    
    for day_offset in range(days):
        current_date = today + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        
        # Find schedule for this day
        day_schedule = next((s for s in schedules if s.day_of_week == day_of_week), None)
        if not day_schedule:
            continue
        
        # Generate time slots
        current_time = datetime.combine(current_date, day_schedule.start_time)
        end_time = datetime.combine(current_date, day_schedule.end_time)
        
        while current_time < end_time:
            # Check if slot is already booked
            existing_appointment = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=current_date,
                appointment_time=current_time.time(),
                status='scheduled'
            ).first()
            
            if not existing_appointment:
                available_slots.append({
                    'date': current_date,
                    'time': current_time.time(),
                    'datetime_str': current_time.strftime('%Y-%m-%d %H:%M')
                })
            
            current_time += timedelta(minutes=day_schedule.slot_duration)
    
    return available_slots

@patient_bp.route('/appointment_history', methods=['GET'])
@login_required
def appointment_history():  # endpoint will be 'patient.appointment_history'
    page = request.args.get('page', 1, type=int)
    appointments = (Appointment.query
                    .filter_by(patient_id=current_user.id)
                    .order_by(Appointment.appointment_date.desc(),
                              Appointment.appointment_time.desc())
                    .paginate(page=page, per_page=10, error_out=False))
    return render_template('appointment_history.html', appointments=appointments)


@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from werkzeug.security import generate_password_hash
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.phone = request.form['phone']
        new_password = request.form.get('new_password')
        if new_password:
            current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    return render_template('profile.html')

def get_available_slots(doctor_id, days=30):
    doctor = Doctor.query.get(doctor_id)
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id).all()
    available_slots = []
    today = datetime.now().date()
    
    for day_offset in range(days):
        current_date = today + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        day_schedule = next((s for s in schedules if s.day_of_week == day_of_week), None)
        
        if not day_schedule:
            continue
        
        current_time = datetime.combine(current_date, day_schedule.start_time)
        end_time = datetime.combine(current_date, day_schedule.end_time)
        
        while current_time < end_time:
            exists = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=current_date,
                appointment_time=current_time.time(),
                status='scheduled'
            ).first()
            if not exists:
                available_slots.append({'date': current_date, 'time': current_time.time(),
                                       'datetime_str': current_time.strftime('%Y-%m-%d %H:%M')})
            current_time += timedelta(minutes=day_schedule.slot_duration)
    return available_slots


@patient_bp.route('/confirm_booking', methods=['POST'])
@login_required
def confirm_booking():
    try:
        doctor_id = int(request.form['doctor_id'])
        appointment_datetime_str = request.form['appointment_datetime']

        # Parse date and time string into datetime object
        appointment_dt = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M')

        # Check if slot is already booked
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_dt.date(),
            appointment_time=appointment_dt.time(),
            status='scheduled'
        ).first()

        if existing:
            flash('This selected slot is already booked. Please select another slot.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

       # Create new appointment
        new_appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            appointment_date=appointment_dt.date(),
            appointment_time=appointment_dt.time(),
            status='scheduled'
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash('Your appointment has been booked successfully!', 'success')
        return redirect(url_for('patient.dashboard'))

    except Exception as e:
        flash('An error occurred while booking the appointment. Please try again.', 'danger')
        return redirect(url_for('patient.view_doctors'))

@patient_bp.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    # cancel logic yahan likhoge
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != current_user.id:
        flash('Unauthorized cancellation attempt.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    # 24 hours pehle hi cancel karo allowed hai
    appointment_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
    if datetime.now() > appointment_dt - timedelta(hours=24):
        flash('Cannot cancel less than 24 hours before appointment.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('patient.dashboard'))