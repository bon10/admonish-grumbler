"""
[interface] ユーザーコントローラ

概要:
  ログインと利用者設定に関するHTTPエンドポイントを定義するFlask Blueprint。
  GET/POST /login(ログイン)、GET /logout(ログアウト)、
  GET/POST /settings(表示名・メール設定)を提供する。
  本アプリの利用者は管理ユーザー1人だけのため、ユーザー登録画面は持たない。
"""

import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.infrastructure.user_repository import UserRepository
from app.usecase.user_interactor import UserInteractor

logger = logging.getLogger(__name__)

bp = Blueprint("user", __name__)
user_interactor = UserInteractor()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index.home"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = user_interactor.authenticate(username, password)
        if not user:
            logger.info("ログイン失敗")
            flash("ユーザー名またはパスワードが違います")
            return redirect(url_for("user.login"))

        login_user(user, remember=True)

        # 表示名・メールアドレスはテンプレートから毎リクエスト参照されるため、
        # ログイン時にセッションへ載せて都度のDB参照を避ける
        session["name"] = user.username
        stored_user = UserRepository().find_by_username(user.username)
        session["email"] = stored_user.email if stored_user else ""

        return redirect(url_for("index.home"))

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    # アプリ側でセッションに載せた情報を先に落としてからログアウトさせる。
    # logout_user()はログイン維持クッキーの破棄指示をセッションに書くため、
    # 後からセッションを触ると破棄指示ごと消してログインが続いてしまう。
    session.pop("name", None)
    session.pop("email", None)
    logout_user()

    flash("ログアウトしました")
    return redirect(url_for("user.login"))


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        if username:
            session["name"] = username
        session["email"] = email

        # メールアドレスは定期サマリーの送信先として使うためDBに永続化する。
        # 表示名は変更できるので、レコードのキーには変わらないログインユーザー名を使う
        UserRepository().update_email(current_user.username, email)

        flash("設定を保存しました")
        return redirect(url_for("user.settings"))

    return render_template("settings.html")
