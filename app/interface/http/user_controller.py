"""
[interface] ユーザーコントローラ

概要:
  ユーザー設定・登録に関するHTTPエンドポイントを定義するFlask Blueprint。
  GET/POST /settings(表示名・メール設定)、GET/POST /signup(新規ユーザー登録)を提供する。
  認証・ログイン機能は現在コメントアウトされており、将来的に有効化予定。
"""

import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import bcrypt
from app.domain.model.user import User
from app.infrastructure.user_repository import UserRepository
from app.usecase.user_interactor import UserAlreadyExistsError, UserInteractor

# from flask_login import current_user, login_user


bp = Blueprint("user", __name__)
user_interactor = UserInteractor()


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        if username:
            session["name"] = username
        session["email"] = email

        # メールアドレスをDBに永続化
        user_repo = UserRepository()
        user_repo.update_email(username, email)

        flash("設定を保存しました")
        return redirect(url_for("user.settings"))
    return render_template("settings.html")


# @login_manager.unauthorized_handler
# def unauthorized():
#     logging.error('unauthorized')
#     return redirect(url_for('user.login'))


# @login_manager.user_loader
# def load_user(user_id):
#     logging.debug('load_user called')
#     logging.debug('session: {}'.format(session))
#     if 'user_id' in session:
#         return User(user_id)
#     else:
#         return None


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    logging.info("signup")
    logging.info(request.form)
    try:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # パスワードのハッシュ化
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            logging.info(password_hash)

            # Userオブジェクトの作成
            user = User(id=id, username=username, password=password_hash)

            # ユーザー登録処理の呼び出し
            user_interactor.register_user(user)
            flash("ユーザー登録が完了しました")

            # ログインページにリダイレクト
            return redirect(url_for("user.login"))
    except UserAlreadyExistsError:
        # エラーが発生した場合の処理
        logging.info("アカウントは既に使用されています")
        flash("アカウント名は既に使用されています")
        return redirect(url_for("user.signup"))

    return render_template("signup.html")


# @bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         # すでにログインしている場合、ホームページへリダイレクト
#         return redirect(url_for('index.home'))

#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         # ユーザー認証処理の呼び出し
#         user = user_interactor.authenticate(username, password)
#         logging.info(user)
#         if user:
#             # ユーザーが存在する場合はセッションにユーザーIDを格納
#             session['user_id'] = str(user.id)
#             session['username'] = user.username
#             session["avatar"] = user.avatar
#             user_model = User(
#                 id=str(user.id),
#                 username=user.username,
#                 password=user.password
#             )
#             login_user(user_model, remember=True)
#             return redirect(url_for('index.home'))
#         else:
#             # ユーザーが存在しない場合はログイン画面にリダイレクト
#             logging.info('ユーザーが存在しません')
#             return redirect(url_for('user.login'))

#     return render_template('login.html')


# @bp.route('/logout', methods=['GET'])
# def logout():
#     ''' ログアウト '''
#     flask_login.logout_user()
#     return 'ログアウトしました'
