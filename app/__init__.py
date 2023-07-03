import os

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from pymongo import MongoClient

bcrypt = Bcrypt()
login_manager = LoginManager()
socketio = SocketIO()


def create_app():
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.BaseConfig')
    app.secret_key = os.getenv('APP_SECRET_KEY')

    bcrypt.init_app(app)

    mongo = MongoClient(os.getenv('MONGO_URI'))
    app.mongo = mongo.get_database('admonish-grumbler-db')

    login_manager.init_app(app)
    login_manager.login_view = "user.login"

    socketio.init_app(app)

    with app.app_context():
        from .interface.http import (index_controller, post_controller,
                                     user_controller)

    app.register_blueprint(user_controller.bp)
    app.register_blueprint(index_controller.bp)
    app.register_blueprint(post_controller.bp)

    return app
