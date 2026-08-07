from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from core.extensions import db
from models import Trek, Booking
from core.decorators import role_required

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/dashboard")
@login_required
@role_required("user")
def dashboard():
    open_treks = Trek.query.filter_by(status="Open").order_by(Trek.start_date).limit(5).all()
    my_bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .limit(5)
        .all()
    )
    booked_count = Booking.query.filter_by(user_id=current_user.id, status="Booked").count()
    return render_template(
        "user/dashboard.html", open_treks=open_treks, my_bookings=my_bookings, booked_count=booked_count
    )


@user_bp.route("/treks")
@login_required
@role_required("user")
def browse_treks():
    query = Trek.query.filter(Trek.status.in_(["Open", "Approved"]))

    search = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "").strip()

    if search:
        query = query.filter(Trek.name.ilike(f"%{search}%"))
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    treks = query.order_by(Trek.start_date).all()

    # IDs of treks this user already booked
    booked_trek_ids = {
        b.trek_id for b in Booking.query.filter_by(user_id=current_user.id, status="Booked").all()
    }

    return render_template(
        "user/treks.html", treks=treks, booked_trek_ids=booked_trek_ids,
        search=search, difficulty=difficulty, location=location,
    )


@user_bp.route("/book/<int:trek_id>", methods=["POST"])
@login_required
@role_required("user")
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user.browse_treks"))

    if trek.available_slots <= 0:
        flash("Sorry, this trek is fully booked.", "danger")
        return redirect(url_for("user.browse_treks"))

    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status="Booked").first()
    if existing:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("user.browse_treks"))

    booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()

    flash(f"Trek '{trek.name}' booked successfully!", "success")
    return redirect(url_for("user.my_bookings"))


@user_bp.route("/bookings")
@login_required
@role_required("user")
def my_bookings():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("user/bookings.html", bookings=bookings)


@user_bp.route("/bookings/cancel/<int:booking_id>", methods=["POST"])
@login_required
@role_required("user")
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash("You cannot cancel this booking.", "danger")
        return redirect(url_for("user.my_bookings"))

    if booking.status == "Booked":
        booking.status = "Cancelled"
        booking.trek.available_slots += 1
        db.session.commit()
        flash("Booking cancelled.", "info")
    else:
        flash("This booking can no longer be cancelled.", "warning")

    return redirect(url_for("user.my_bookings"))


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("user")
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name:
            flash("Name cannot be empty.", "danger")
            return render_template("user/profile.html")

        current_user.name = name
        current_user.phone = phone

        new_password = request.form.get("new_password", "")
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html")
