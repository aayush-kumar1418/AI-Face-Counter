 AI Face Counter

An AI-powered web application that detects and counts human faces in real time using your webcam or from uploaded images — built with Flask, OpenCV, and SQLAlchemy.

 Features


 User Authentication — Register and log in securely (Werkzeug password hashing)
 Live Webcam Detection — Real-time face detection and counting via OpenCV
 Image Upload Detection — Upload an image and get face-count results with annotated bounding boxes
 Detection History — Every detection is logged per-user with timestamp and face count
 Persistent Storage — SQLite database via SQLAlchemy ORM
 Responsive UI — Clean Bootstrap 5 interface


 Tech Stack

LayerTechnologyBackendFlask, Flask-SQLAlchemyComputer VisionOpenCV (Haar Cascade Classifier)DatabaseSQLiteFrontendJinja2, Bootstrap 5AuthWerkzeug Security (password hashing)DeploymentGunicorn / Vercel-ready

 Project Structure

AI-Face-Counter/
├── app.py                 # Application factory & entry point
├── config.py               # App configuration
├── models/                 # SQLAlchemy models (User, Detection)
├── routes/                 # Blueprints: auth, main, detect
├── utils/                  # Database init, face detector, webcam handler
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, uploaded & detected images
├── requirements.txt
├── Procfile                 # For Gunicorn deployment
└── vercel.json               # Vercel deployment config

 Getting Started

Prerequisites


Python 3.10+
pip


Installation

bash# Clone the repository
git clone https://github.com/<your-username>/ai-face-counter.git
cd ai-face-counter

# Install dependencies
python -m pip install -r requirements.txt

Run the app

bashpython app.py


 How It Works


Register/login to your account.
From the dashboard, choose Face Counter (live webcam) or Upload Image.
OpenCV's Haar Cascade classifier detects faces and draws bounding boxes.
The result — including face count and annotated image — is saved to your detection history.


 Roadmap / Ideas for Contribution


 Switch to a DNN-based face detector for higher accuracy
 Add REST API endpoints for programmatic detection
 Docker support
 Cloud storage integration for detected images


 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

 License

This project is open source and available under the MIT License.


 If you found this project useful, consider giving it a star!
