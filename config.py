import os
import tempfile
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'FaceCounter@123')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    if os.environ.get('VERCEL'):
        DATA_DIR = Path(tempfile.gettempdir()) / 'face_counter'
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(DATA_DIR / 'database.db').as_posix()}"
        UPLOAD_FOLDER = str(DATA_DIR / 'uploads')
        DETECTED_FOLDER = str(DATA_DIR / 'detected')
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
        DETECTED_FOLDER = os.path.join(BASE_DIR, 'static', 'detected')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
