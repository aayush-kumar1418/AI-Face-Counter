from pathlib import Path

base = Path(r"c:\Users\User\OneDrive\Desktop\AI Face Counter using OpenCV and Machine Learning\FaceCounterProject")
files = {
    "app.py": """from flask import Flask
from config import Config
from utils.database import db
from routes.auth import auth
from routes.main import main
from routes.detect import detect
import os


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    db.init_app(app)

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.DETECTED_FOLDER, exist_ok=True)

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(detect)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
""",
    "config.py": """import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'FaceCounter@123')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DETECTED_FOLDER = os.path.join(BASE_DIR, 'static', 'detected')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
""",
    "requirements.txt": """Flask==3.1.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
opencv-python==4.11.0.46
numpy==2.5.0
""",
    "routes/__init__.py": """# Route package initializer""",
    "routes/auth.py": """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from utils.database import db
from models.user import User

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not fullname or not email or not password:
            flash('Please fill in all required fields.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'warning')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'warning')
            return render_template('register.html')

        user = User(fullname=fullname, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.fullname
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
""",
    "routes/main.py": """from flask import Blueprint, render_template, session, redirect, url_for

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('index.html')


@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    return render_template('dashboard.html', user=session.get('user_name', 'Guest'))


@main.route('/about')
def about():
    return render_template('about.html')
""",
    "routes/detect.py": """import os
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename

from utils.camera import run_camera
from utils.detector import detect_faces
from utils.database import db
from models.detection import Detection


detect = Blueprint('detect', __name__)


 def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})


@detect.route('/face-counter')
def webcam():
    if 'user_id' not in session:
        flash('Please log in to access the face counter.', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('webcam.html')


@detect.route('/start-camera')
def start_camera():
    if 'user_id' not in session:
        flash('Please log in to access the face counter.', 'warning')
        return redirect(url_for('auth.login'))

    flash("The camera is opening. Press 'q' to close.", 'info')
    run_camera()
    flash('Camera session ended.', 'success')
    return redirect(url_for('detect.webcam'))


@detect.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please log in to upload images.', 'warning')
        return redirect(url_for('auth.login'))

    result = None

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('Please choose an image to upload.', 'warning')
            return redirect(url_for('detect.upload'))

        image_file = request.files['image']

        if image_file.filename == '':
            flash('Please choose an image file.', 'warning')
            return redirect(url_for('detect.upload'))

        if not allowed_file(image_file.filename):
            flash('Only PNG, JPG, JPEG and GIF images are allowed.', 'warning')
            return redirect(url_for('detect.upload'))

        filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{image_file.filename}")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        detected_path = os.path.join(current_app.config['DETECTED_FOLDER'], filename)

        image_file.save(upload_path)
        faces = detect_faces(upload_path, detected_path)

        record = Detection(user_id=session['user_id'], filename=filename, face_count=faces)
        db.session.add(record)
        db.session.commit()

        result = {'filename': filename, 'count': faces}
        flash(f'Detected {faces} face{'s' if faces != 1 else ''}.', 'success')

    return render_template('upload.html', result=result)


@detect.route('/history')
def history():
    if 'user_id' not in session:
        flash('Please log in to view your history.', 'warning')
        return redirect(url_for('auth.login'))

    records = Detection.query.filter_by(user_id=session['user_id']).order_by(Detection.created_at.desc()).all()
    return render_template('history.html', records=records)
""",
    "models/__init__.py": """from .user import User
from .detection import Detection
""",
    "models/detection.py": """from datetime import datetime
from utils.database import db


class Detection(db.Model):
    __tablename__ = 'detections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    face_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='detections')
""",
    "utils/detector.py": """import cv2
import os


def detect_faces(image_path, output_path=None):
    if not os.path.exists(image_path):
        raise ValueError('Image file does not exist.')

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError('Could not read the image file.')

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, image)

    return len(faces)
""",
    "templates/base.html": """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>{% block title %}AI Face Counter{% endblock %}</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
    <link rel='stylesheet' href='{{ url_for('static', filename='css/style.css') }}'>
</head>
<body>
<nav class='navbar navbar-expand-lg navbar-dark bg-dark'>
    <div class='container'>
        <a class='navbar-brand fw-bold' href='{{ url_for('main.home') }}'>AI Face Counter</a>
        <button class='navbar-toggler' type='button' data-bs-toggle='collapse' data-bs-target='#navbarNav'>
            <span class='navbar-toggler-icon'></span>
        </button>
        <div class='collapse navbar-collapse' id='navbarNav'>
            <ul class='navbar-nav ms-auto'>
                <li class='nav-item'><a class='nav-link' href='{{ url_for('main.home') }}'>Home</a></li>
                <li class='nav-item'><a class='nav-link' href='{{ url_for('main.about') }}'>About</a></li>
                {% if session.get('user_id') %}
                <li class='nav-item'><a class='nav-link' href='{{ url_for('main.dashboard') }}'>Dashboard</a></li>
                <li class='nav-item'><a class='nav-link' href='{{ url_for('auth.logout') }}'>Logout</a></li>
                {% else %}
                <li class='nav-item'><a class='nav-link' href='{{ url_for('auth.login') }}'>Login</a></li>
                <li class='nav-item'><a class='nav-link' href='{{ url_for('auth.register') }}'>Register</a></li>
                {% endif %}
            </ul>
        </div>
    </div>
</nav>
<div class='container my-4'>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class='alert alert-{{ category }} alert-dismissible fade show' role='alert'>
                    {{ message }}
                    <button type='button' class='btn-close' data-bs-dismiss='alert'></button>
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</div>
<script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'></script>
</body>
</html>
""",
    "templates/login.html": """{% extends 'base.html' %}
{% block title %}Login - Face Counter{% endblock %}
{% block content %}
<div class='row justify-content-center'>
    <div class='col-md-6'>
        <div class='card shadow-sm p-4'>
            <h2 class='mb-4 text-center'>Login</h2>
            <form method='POST' action='{{ url_for('auth.login') }}'>
                <div class='mb-3'>
                    <label class='form-label'>Email</label>
                    <input type='email' class='form-control' name='email' placeholder='Enter your email' required>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Password</label>
                    <input type='password' class='form-control' name='password' placeholder='Enter your password' required>
                </div>
                <button class='btn btn-primary w-100' type='submit'>Login</button>
            </form>
            <p class='mt-3 text-center'>Don't have an account? <a href='{{ url_for('auth.register') }}'>Register here</a></p>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/register.html": """{% extends 'base.html' %}
{% block title %}Register - Face Counter{% endblock %}
{% block content %}
<div class='row justify-content-center'>
    <div class='col-md-7 col-lg-5'>
        <div class='card shadow-sm p-4'>
            <h2 class='mb-4 text-center'>Create Account</h2>
            <form method='POST' action='{{ url_for('auth.register') }}'>
                <div class='mb-3'>
                    <label class='form-label'>Full Name</label>
                    <input type='text' class='form-control' name='fullname' placeholder='Enter your full name' required>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Email</label>
                    <input type='email' class='form-control' name='email' placeholder='Enter your email' required>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Password</label>
                    <input type='password' class='form-control' name='password' placeholder='Enter a password' required>
                </div>
                <div class='mb-3'>
                    <label class='form-label'>Confirm Password</label>
                    <input type='password' class='form-control' name='confirm_password' placeholder='Confirm your password' required>
                </div>
                <button class='btn btn-success w-100' type='submit'>Register</button>
            </form>
            <p class='mt-3 text-center'>Already have an account? <a href='{{ url_for('auth.login') }}'>Login</a></p>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/dashboard.html": """{% extends 'base.html' %}
{% block title %}Dashboard - Face Counter{% endblock %}
{% block content %}
<div class='text-center'>
    <h1 class='display-5'>Welcome, {{ user }}!</h1>
    <p class='lead'>Use the buttons below to start face detection with your webcam or upload an image.</p>
    <div class='d-flex flex-column gap-3 align-items-center mt-4'>
        <a href='{{ url_for('detect.webcam') }}' class='btn btn-primary btn-lg'>Face Counter</a>
        <a href='{{ url_for('detect.upload') }}' class='btn btn-outline-secondary btn-lg'>Upload Image</a>
        <a href='{{ url_for('detect.history') }}' class='btn btn-outline-info btn-lg'>Detection History</a>
    </div>
</div>
{% endblock %}
""",
    "templates/webcam.html": """{% extends 'base.html' %}
{% block title %}Live Camera - Face Counter{% endblock %}
{% block content %}
<div class='row justify-content-center'>
    <div class='col-lg-8'>
        <div class='card shadow-sm p-4'>
            <h2 class='mb-3'>Live Face Counter</h2>
            <p>Click the button below to open your machine's webcam. Press <strong>q</strong> inside the camera window to close it.</p>
            <a href='{{ url_for('detect.start_camera') }}' class='btn btn-success btn-lg'>Start Camera</a>
            <hr>
            <p>Alternatively, upload an image for face detection.</p>
            <a href='{{ url_for('detect.upload') }}' class='btn btn-outline-primary mt-3'>Upload Image</a>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/upload.html": """{% extends 'base.html' %}
{% block title %}Upload Image - Face Counter{% endblock %}
{% block content %}
<div class='row justify-content-center'>
    <div class='col-md-8'>
        <div class='card shadow-sm p-4'>
            <h2 class='mb-3'>Upload an Image</h2>
            <form method='POST' enctype='multipart/form-data'>
                <div class='mb-3'>
                    <label class='form-label'>Choose Image</label>
                    <input type='file' class='form-control' name='image' accept='image/*' required>
                </div>
                <button class='btn btn-primary' type='submit'>Detect Faces</button>
            </form>
        </div>
    </div>
</div>

{% if result %}
<div class='row justify-content-center mt-4'>
    <div class='col-md-8'>
        <div class='card shadow-sm p-4'>
            <h3>Result</h3>
            <p>Detected <strong>{{ result.count }}</strong> face{{ 's' if result.count != 1 else '' }}.</p>
            <div class='text-center'>
                <img src='{{ url_for('static', filename='detected/' + result.filename) }}' class='img-fluid rounded' alt='Detected image'>
            </div>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}
""",
    "templates/history.html": """{% extends 'base.html' %}
{% block title %}History - Face Counter{% endblock %}
{% block content %}
<div class='card shadow-sm p-4'>
    <h2 class='mb-3'>Detection History</h2>
    {% if not records %}
        <p>No detection history found yet. Upload an image to start tracking your detections.</p>
        <a href='{{ url_for('detect.upload') }}' class='btn btn-primary'>Upload Image</a>
    {% else %}
        <div class='table-responsive'>
            <table class='table table-striped align-middle'>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Image</th>
                        <th>Faces</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                        <tr>
                            <td>{{ record.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                            <td><a href='{{ url_for('static', filename='detected/' + record.filename) }}' target='_blank'>View</a></td>
                            <td>{{ record.face_count }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    {% endif %}
</div>
{% endblock %}
""",
    "templates/about.html": """{% extends 'base.html' %}
{% block title %}About - Face Counter{% endblock %}
{% block content %}
<div class='card shadow-sm p-4'>
    <h2>About AI Face Counter</h2>
    <p>This project uses Flask, OpenCV, and SQLAlchemy to detect and count faces from images and your webcam.</p>
    <p>Sign in and use the dashboard buttons to start face detection.</p>
</div>
{% endblock %}
""",
    "static/css/style.css": """body {
    background: #f8f9fa;
}
.card {
    border: none;
}
.navbar-brand {
    letter-spacing: 0.05em;
}
img {
    max-width: 100%;
}
""",
    "README.md": """# AI Face Counter

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.
""",
}

for relative, content in files.items():
    target = base / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

print('Files written successfully.')
