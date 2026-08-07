from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from core.extensions import db
from models import User, Trek, Booking
from core.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def restrict_to_admin():
    if current_user.role != "admin":
        from flask import abort
        abort(403)


@admin_bp.route("/dashboard")
def dashboard():
    stats = {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role="user").count(),
        "total_staff": User.query.filter_by(role="staff").count(),
        "total_bookings": Booking.query.count(),
        "pending_staff": User.query.filter_by(role="staff", is_approved=False, is_blacklisted=False).count(),
    }
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, recent_bookings=recent_bookings)


# ---------- Trek management ----------

@admin_bp.route("/treks")
def treks():
    all_treks = Trek.query.order_by(Trek.created_at.desc()).all()
    return render_template("admin/treks.html", treks=all_treks)


@admin_bp.route("/treks/add", methods=["GET", "POST"])
def add_trek():
    if request.method == "POST":
        error = _save_trek_form()
        if error:
            flash(error, "danger")
            return render_template("admin/trek_form.html", trek=None)
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin.treks"))
    return render_template("admin/trek_form.html", trek=None)


@admin_bp.route("/treks/edit/<int:trek_id>", methods=["GET", "POST"])
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if request.method == "POST":
        error = _save_trek_form(trek)
        if error:
            flash(error, "danger")
            return render_template("admin/trek_form.html", trek=trek)
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.treks"))
    return render_template("admin/trek_form.html", trek=trek)


@admin_bp.route("/treks/delete/<int:trek_id>", methods=["POST"])
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek removed.", "info")
    return redirect(url_for("admin.treks"))


def _save_trek_form(trek=None):
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    difficulty = request.form.get("difficulty", "")
    duration = request.form.get("duration", "")
    total_slots = request.form.get("total_slots", "")
    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")
    description = request.form.get("description", "").strip()

    if not all([name, location, difficulty, duration, total_slots, start_date, end_date]):
        return "All required fields must be filled."

    try:
        duration = int(duration)
        total_slots = int(total_slots)
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid number or date format."

    if duration <= 0 or total_slots <= 0:
        return "Duration and slots must be positive numbers."
    if end_date < start_date:
        return "End date cannot be before start date."

    if trek is None:
        trek = Trek(
            name=name, location=location, difficulty=difficulty, duration=duration,
            total_slots=total_slots, available_slots=total_slots,
            start_date=start_date, end_date=end_date, description=description,
            status="Pending",
        )
        db.session.add(trek)
    else:
        # Keep availaable_slots consistent if total_slots changes
        booked = trek.booked_slots
        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.duration = duration
        trek.total_slots = total_slots
        trek.available_slots = max(total_slots - booked, 0)
        trek.start_date = start_date
        trek.end_date = end_date
        trek.description = description

    db.session.commit()
    return None


@admin_bp.route("/treks/assign/<int:trek_id>", methods=["GET", "POST"])
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    approved_staff = User.query.filter_by(role="staff", is_approved=True, is_blacklisted=False).all()

    if request.method == "POST":
        staff_id = request.form.get("staff_id")
        if not staff_id:
            flash("Please select a staff member.", "danger")
            return render_template("admin/assign_staff.html", trek=trek, staff_list=approved_staff)

        trek.assigned_staff_id = int(staff_id)
        if trek.status == "Pending":
            trek.status = "Approved"
        db.session.commit()
        flash("Staff assigned successfully.", "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/assign_staff.html", trek=trek, staff_list=approved_staff)




@admin_bp.route("/staff")
def staff_list():
    staff = User.query.filter_by(role="staff").order_by(User.created_at.desc()).all()
    return render_template("admin/staff.html", staff=staff)


@admin_bp.route("/staff/approve/<int:staff_id>", methods=["POST"])
def approve_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.is_approved = True
    db.session.commit()
    flash(f"{staff.name} approved as trek staff.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/blacklist/<int:staff_id>", methods=["POST"])
def blacklist_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.is_blacklisted = not staff.is_blacklisted
    db.session.commit()
    status = "blacklisted" if staff.is_blacklisted else "reinstated"
    flash(f"{staff.name} has been {status}.", "warning")
    return redirect(url_for("admin.staff_list"))




@admin_bp.route("/users")
def users_list():
    users = User.query.filter_by(role="user").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/blacklist/<int:user_id>", methods=["POST"])
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    status = "blacklisted" if user.is_blacklisted else "reinstated"
    flash(f"{user.name} has been {status}.", "warning")
    return redirect(url_for("admin.users_list"))



@admin_bp.route("/bookings")
def bookings():
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/bookings.html", bookings=all_bookings)


@admin_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "treks")

    trek_results, staff_results, user_results = [], [], []

    if query:
        like = f"%{query}%"
        if category == "treks":
            filters = [Trek.name.ilike(like), Trek.location.ilike(like)]
            if query.isdigit():
                filters.append(Trek.id == int(query))
            trek_results = Trek.query.filter(db.or_(*filters)).all()
        elif category == "staff":
            filters = [User.name.ilike(like), User.email.ilike(like)]
            if query.isdigit():
                filters.append(User.id == int(query))
            staff_results = User.query.filter(User.role == "staff", db.or_(*filters)).all()
        elif category == "users":
            filters = [User.name.ilike(like), User.email.ilike(like)]
            if query.isdigit():
                filters.append(User.id == int(query))
            user_results = User.query.filter(User.role == "user", db.or_(*filters)).all()

    return render_template(
        "admin/search.html",
        query=query,
        category=category,
        trek_results=trek_results,
        staff_results=staff_results,
        user_results=user_results,
    )
