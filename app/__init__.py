"""
[infrastructure] Flaskアプリケーションファクトリ

概要:
  create_app()でFlaskアプリの初期化を行う。
  DB接続(MongoDB)、Blueprint登録、スケジューラ起動、ログインセッションの初期化を担当する。
  アプリケーション全体のエントリーポイント。
"""

import os

from dotenv import load_dotenv
from flask import Flask, redirect, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from pymongo import MongoClient

bcrypt = Bcrypt()
login_manager = LoginManager()

# ログインしていなくてもアクセスできるエンドポイント。
# user.loginはログイン導線そのもの、staticはログイン画面のCSS配信のため除外する。
PUBLIC_ENDPOINTS = {"user.login", "static"}


def create_app():
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    bcrypt.init_app(app)

    mongo = MongoClient(os.getenv("MONGO_URI"))
    app.mongo = mongo.get_database("admonish-grumbler-db")

    login_manager.init_app(app)
    login_manager.login_view = "user.login"

    with app.app_context():
        from .interface.http import (
            dashboard_controller,
            index_controller,
            post_controller,
            search_controller,
            summary_controller,
            user_controller,
        )

    app.register_blueprint(user_controller.bp)
    app.register_blueprint(index_controller.bp)
    app.register_blueprint(post_controller.bp)
    app.register_blueprint(summary_controller.bp)
    app.register_blueprint(dashboard_controller.bp)
    app.register_blueprint(search_controller.bp)

    # Initialize APScheduler for periodic summary generation
    # Flaskのreloaderは親プロセス+子プロセスの2重起動になるため、
    # 子プロセス(実際にリクエストを処理する側)でのみスケジューラを起動する
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from .scheduler import init_scheduler

        init_scheduler(app)

    @app.before_request
    def require_login():
        """
        全リクエストをまとめてログイン必須にする。

        本アプリは管理ユーザー1人しか使わず全画面が非公開のため、
        画面ごとにデコレータを付けて回るより、既定を非公開にして
        例外だけを列挙するほうが付け忘れによる情報露出を防げる。
        """
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if not current_user.is_authenticated:
            return redirect(url_for("user.login"))
        return None

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.usecase.user_interactor import UserInteractor

    return UserInteractor().find_login_user(user_id)
