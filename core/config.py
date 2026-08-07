import os

# core/config.py lives one level below the project root, so go up one directory,
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = "trek-management-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pre-existing admin credentials (seeded automatically on first run)
    ADMIN_EMAIL = "admin@trekapp.com"
    ADMIN_PASSWORD = "Admin@123"
    ADMIN_NAME = "System Admin"
