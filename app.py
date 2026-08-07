from flask import Flask, render_template

from core.config import Config
from core.extensions import db, login_manager
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.staff import staff_bp
    from blueprints.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    with app.app_context():
        db.create_all()
        seed_admin(app)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_admin(app):
    """Create the pre-existing Admin account if it doesn't already exist."""
    existing = User.query.filter_by(role="admin").first()
    if existing:
        return
    admin = User(
        name=app.config["ADMIN_NAME"],
        email=app.config["ADMIN_EMAIL"],
        role="admin",
        is_approved=True,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    print(f"[seed] Admin account created -> {app.config['ADMIN_EMAIL']} / {app.config['ADMIN_PASSWORD']}")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
