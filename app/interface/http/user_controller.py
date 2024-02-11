import logging

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import current_user, login_user

from app import bcrypt, login_manager
from app.domain.model.user import User
from app.usecase.user_interactor import UserAlreadyExistsError, UserInteractor

bp = Blueprint('user', __name__)
user_interactor = UserInteractor()


@login_manager.unauthorized_handler
def unauthorized():
    logging.error('unauthorized')
    return redirect(url_for('user.login'))


@login_manager.user_loader
def load_user(user_id):
    logging.debug('load_user called')
    logging.debug('session: {}'.format(session))
    if 'user_id' in session:
        return User(user_id)
    else:
        return None


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    logging.info('signup')
    logging.info(request.form)
    try:
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")

            # パスワードのハッシュ化
            password_hash = bcrypt.generate_password_hash(
                password).decode('utf-8')
            logging.info(password_hash)

            # Userオブジェクトの作成
            user = User(id=id, username=username, password=password_hash)

            # ユーザー登録処理の呼び出し
            user_interactor.register_user(user)
            flash("ユーザー登録が完了しました")

            # ログインページにリダイレクト
            return redirect(url_for('user.login'))
    except UserAlreadyExistsError:
        # エラーが発生した場合の処理
        logging.info('アカウントは既に使用されています')
        flash("アカウント名は既に使用されています")
        return redirect(url_for('user.signup'))

    return render_template('signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # すでにログインしている場合、ホームページへリダイレクト
        return redirect(url_for('index.home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ユーザー認証処理の呼び出し
        user = user_interactor.authenticate(username, password)
        logging.info(user)
        if user:
            # ユーザーが存在する場合はセッションにユーザーIDを格納
            session['user_id'] = str(user.id)
            session['username'] = user.username
            session["avatar"] = user.avatar
            user_model = User(
                id=str(user.id),
                username=user.username,
                password=user.password
            )
            login_user(user_model, remember=True)
            return redirect(url_for('index.home'))
        else:
            # ユーザーが存在しない場合はログイン画面にリダイレクト
            logging.info('ユーザーが存在しません')
            return redirect(url_for('user.login'))

    return render_template('login.html')


@bp.route('/logout', methods=['GET'])
def logout():
    ''' ログアウト '''
    flask_login.logout_user()
    return 'ログアウトしました'
