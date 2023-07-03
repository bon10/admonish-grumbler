import flask_login
from flask import Blueprint, render_template
from flask_socketio import SocketIO, emit

from app import socketio
from app.usecase.post_interactor import PostInteractor

bp = Blueprint('index', __name__)
post_interactor = PostInteractor()


@bp.route('/')
@flask_login.login_required
def home():
    posts = post_interactor.get_all_posts()  # 投稿データを取得
    return render_template('index.html', posts=posts)


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('new_message')
def handle_new_message(message):
    print('New message:', message)
    # ここで新しいメッセージを処理し、他のクライアントに送信するなどの処理を行う
