import flask_login
from flask import Blueprint, render_template

from app.usecase.post_interactor import PostInteractor

bp = Blueprint('index', __name__)
post_interactor = PostInteractor()


@bp.route('/')
@flask_login.login_required
def home():
    posts = post_interactor.get_all_posts()  # 投稿データを取得
    return render_template('index.html', posts=posts)
