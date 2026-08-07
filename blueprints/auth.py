from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from core.extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


def _redirect_for_role(role, is_approved=True):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "staff":
        if not is_approved:
            return redirect(url_for("staff.pending_approval"))
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("user.dashboard"))


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user.role, current_user.is_approved)
    return render_template("index.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user.role, current_user.is_approved)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        if user.is_blacklisted:
            flash("Your account has been blacklisted. Contact the admin.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")
        return _redirect_for_role(user.role, user.is_approved)

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register_user():
    """Self-registration for trekkers (auto-approved)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = _validate_registration(name, email, password, confirm)
        if error:
            flash(error, "danger")
            return render_template("auth/register_user.html")

        new_user = User(name=name, email=email, phone=phone, role="user", is_approved=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_user.html")


@auth_bp.route("/register/staff", methods=["GET", "POST"])
def register_staff():
    """Self-registration for trek staff. Requires admin approval before dashboard access."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = _validate_registration(name, email, password, confirm)
        if error:
            flash(error, "danger")
            return render_template("auth/register_staff.html")

        new_staff = User(name=name, email=email, phone=phone, role="staff", is_approved=False)
        new_staff.set_password(password)
        db.session.add(new_staff)
        db.session.commit()

        flash("Registration submitted! You can log in once the admin approves your account.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_staff.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def _validate_registration(name, email, password, confirm):
    if not name or not email or not password:
        return "All required fields must be filled."
    if password != confirm:
        return "Passwords do not match."
    if User.query.filter_by(email=email).first():
        return "An account with this email already exists."
    if User.query.filter_by(email=email).first():
        return "An account with this email already exists."
   
    return None
