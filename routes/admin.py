from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import Doctor, Appointment, User, DoctorSchedule, db
from datetime import datetime, time
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required!', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    # Enhanced dashboard statistics
    total_doctors = Doctor.query.filter_by(is_available=True).count()
    total_patients = User.query.filter_by(role='patient').count()
    
    today = datetime.now().date()
    today_appointments = Appointment.query.filter_by(
        appointment_date=today,
        status='scheduled'
    ).count()
    
    # Monthly stats
    this_month = datetime.now().replace(day=1).date()
    monthly_appointments = Appointment.query.filter(
        Appointment.appointment_date >= this_month
    ).count()
    
    # Recent appointments
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(10).all()
    
    # Popular specializations
    popular_specs = db.session.query(
        Doctor.specialization,
        func.count(Appointment.id).label('count')
    ).join(Appointment).group_by(Doctor.specialization).order_by(
        func.count(Appointment.id).desc()
    ).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         today_appointments=today_appointments,
                         monthly_appointments=monthly_appointments,
                         recent_appointments=recent_appointments,
                         popular_specs=popular_specs)

@admin_bp.route('/admin/doctors')
@login_required
@admin_required
def manage_doctors():
    doctors = Doctor.query.all()
    return render_template('manage_doctors.html', doctors=doctors)

@admin_bp.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    if request.method == 'POST':
        doctor = Doctor(
            name=request.form['name'],
            specialization=request.form['specialization'],
            email=request.form['email'],
            phone=request.form['phone'],
            experience=int(request.form['experience']),
            qualifications=request.form['qualifications']
        )
        
        db.session.add(doctor)
        db.session.commit()
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin.manage_doctors'))
    
    return render_template('add_doctor.html')

# NEW: Edit Doctor
@admin_bp.route('/admin/doctor/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        doctor.name = request.form['name']
        doctor.specialization = request.form['specialization']
        doctor.email = request.form['email']
        doctor.phone = request.form['phone']
        doctor.experience = int(request.form['experience'])
        doctor.qualifications = request.form['qualifications']
        doctor.is_available = 'is_available' in request.form
        
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.manage_doctors'))
    
    return render_template('edit_doctor.html', doctor=doctor)

# NEW: Delete Doctor
@admin_bp.route('/admin/doctor/<int:doctor_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Check if doctor has any scheduled appointments
    active_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        status='scheduled'
    ).count()
    
    if active_appointments > 0:
        flash('Cannot delete doctor with active appointments!', 'error')
        return redirect(url_for('admin.manage_doctors'))
    
    db.session.delete(doctor)
    db.session.commit()
    
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('admin.manage_doctors'))

# NEW: Doctor Schedule Management
@admin_bp.route('/admin/doctor/<int:doctor_id>/schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_doctor_schedule(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        # Clear existing schedules
        DoctorSchedule.query.filter_by(doctor_id=doctor_id).delete()
        
        # Add new schedules
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day_idx, day in enumerate(days):
            start_time_str = request.form.get(f'{day}_start_time')
            end_time_str = request.form.get(f'{day}_end_time')
            
            if start_time_str and end_time_str:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                schedule = DoctorSchedule(
                    doctor_id=doctor_id,
                    day_of_week=day_idx,
                    start_time=start_time,
                    end_time=end_time,
                    slot_duration=int(request.form.get('slot_duration', 30))
                )
                db.session.add(schedule)
        
        db.session.commit()
        flash('Schedule updated successfully!', 'success')
        return redirect(url_for('admin.manage_doctors'))
    
    # Get existing schedules
    schedules = {s.day_of_week: s for s in DoctorSchedule.query.filter_by(doctor_id=doctor_id).all()}
    
    return render_template('doctor_schedule.html', doctor=doctor, schedules=schedules)

@admin_bp.route('/admin/appointments')
@login_required
@admin_required
def view_all_appointments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Appointment.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter)
