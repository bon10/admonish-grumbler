from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)

from app import bcrypt
from app.domain.model.user import User
from app.usecase.user_interactor import UserInteractor

bp = Blueprint('user', __name__)
user_interactor = UserInteractor()

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # パスワードのハッシュ化
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')  # 修正

        # Userオブジェクトの作成
        user = User(username, password_hash)

        # ユーザー登録処理の呼び出し
        user_interactor.register_user(user)

        # ログインページにリダイレクト
        return redirect(url_for('user.login'))

    return render_template('signup.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ユーザー認証処理の呼び出し
        user = user_interactor.authenticate(username, password)

        if user:
            # ユーザーが存在する場合はセッションにユーザーIDを格納
            session['user_id'] = user.id
            return redirect(url_for('user.profile'))
        else:
            # ユーザーが存在しない場合はログイン画面にリダイレクト
            return redirect(url_for('user.login'))

    return render_template('login.html')