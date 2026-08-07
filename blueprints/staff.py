from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from core.extensions import db
from models import Trek, Booking, User
from core.decorators import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

VALID_STATUSES = ["Approved", "Open", "Closed", "Completed"]


@staff_bp.route("/dashboard")
@login_required
@role_required("staff")
def dashboard():
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date).all()
    return render_template("staff/dashboard.html", treks=treks)


@staff_bp.route("/pending")
@login_required
def pending_approval():
    # Shown to staff whose registration is not yet approved by admin.
    if current_user.role != "staff" or current_user.is_approved:
        return redirect(url_for("auth.index"))
    return render_template("staff/pending.html")


@staff_bp.route("/trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
@role_required("staff")
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        abort(403)

    if request.method == "POST":
        new_status = request.form.get("status")
        new_slots = request.form.get("available_slots")

        if new_status and new_status in VALID_STATUSES:
            trek.status = new_status

        if new_slots is not None and new_slots != "":
            try:
                new_slots = int(new_slots)
                if 0 <= new_slots <= trek.total_slots:
                    trek.available_slots = new_slots
                else:
                    flash(f"Available slots must be between 0 and {trek.total_slots}.", "danger")
                    return redirect(url_for("staff.trek_detail", trek_id=trek.id))
            except ValueError:
                flash("Invalid slot number.", "danger")
                return redirect(url_for("staff.trek_detail", trek_id=trek.id))

        db.session.commit()
        flash("Trek updated.", "success")
        return redirect(url_for("staff.trek_detail", trek_id=trek.id))

    participants = (
        db.session.query(Booking, User)
        .join(User, Booking.user_id == User.id)
        .filter(Booking.trek_id == trek.id, Booking.status != "Cancelled")
        .all()
    )
    return render_template("staff/trek_detail.html", trek=trek, participants=participants, statuses=VALID_STATUSES)
