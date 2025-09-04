# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Yeh db instance COMMON hai sabke liye
db = SQLAlchemy()

# Import all models so they're registered
from .user import User
from .doctor import Doctor , DoctorSchedule
from .appointment import Appointment
