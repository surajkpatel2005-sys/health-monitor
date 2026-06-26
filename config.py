"""
Configuration file for Personal Health & Wellness Monitoring System
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask Secret Key (used for session signing)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'health_monitor_super_secret_key_2024')

    # ---------------- MySQL Database Configuration ----------------
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '09122006')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'health_monitor_db')
    MYSQL_CURSORCLASS = 'DictCursor'

    # ---------------- File Upload Configuration ----------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    # ---------------- Session Configuration ----------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # 24 hours

    # ---------------- App Settings ----------------
    DEBUG = True
