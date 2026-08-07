from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from core.extensions import db


class User(db.Model, UserMixin):
    """Single table for Admin, Trek Staff, and Trekkers, distinguished by `role`."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # 'admin' | 'staff' | 'user'

    # Staff must be approved by admin before they can access their dashboard.
    # Regular users are approved automatically at registration.
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_treks = db.relationship(
        "Trek", backref="assigned_staff", foreign_keys="Trek.assigned_staff_id"
    )
    bookings = db.relationship(
        "Booking", backref="trekker", foreign_keys="Booking.user_id"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        # Overrides Flask-Login's UserMixin default (always True).
        # Blacklisted accounts cannot log in at all.
        return not self.is_blacklisted

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy / Moderate / Hard
    duration = db.Column(db.Integer, nullable=False)  # in days
    description = db.Column(db.Text)

    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Pending -> Approved (staff assigned) -> Open -> Closed / Completed
    status = db.Column(db.String(20), nullable=False, default="Pending")

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="trek", cascade="all, delete-orphan")

    @property
    def booked_slots(self):
        return self.total_slots - self.available_slots

    @property
    def is_upcoming(self):
        return self.start_date >= date.today()

    def __repr__(self):
        return f"<Trek {self.name} ({self.status})>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)

    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="Booked")  # Booked / Cancelled / Completed

    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id} ({self.status})>"
