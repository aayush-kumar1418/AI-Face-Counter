from flask import Flask
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
