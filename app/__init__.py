"""
[infrastructure] Flaskアプリケーションファクトリ

概要:
  create_app()でFlaskアプリの初期化を行う。
  DB接続(MongoDB)、Blueprint登録、スケジューラ起動、セッション初期化を担当。
  アプリケーション全体のエントリーポイント。
"""
import os
import random
import string

from dotenv import load_dotenv
from flask import Flask, session
from flask_bcrypt import Bcrypt

# from flask_login import LoginManager
from pymongo import MongoClient

bcrypt = Bcrypt()
# login_manager = LoginManager()


def create_app():
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.BaseConfig")
    app.secret_key = os.getenv("APP_SECRET_KEY")

    bcrypt.init_app(app)

    mongo = MongoClient(os.getenv("MONGO_URI"))
    app.mongo = mongo.get_database("admonish-grumbler-db")

    # ogin_manager.init_app(app)
    # login_manager.login_view = "user.login"

    with app.app_context():
        from .interface.http import index_controller, post_controller, summary_controller, user_controller

    app.register_blueprint(user_controller.bp)
    app.register_blueprint(index_controller.bp)
    app.register_blueprint(post_controller.bp)
    app.register_blueprint(summary_controller.bp)

    # Initialize APScheduler for periodic summary generation
    from .scheduler import init_scheduler
    init_scheduler(app)

    @app.before_request
    def init_session():
        if "name" not in session:
            session["name"] = "".join(
                random.choices(string.ascii_letters + string.digits, k=12)
            )
        if "email" not in session:
            session["email"] = ""

    return app
