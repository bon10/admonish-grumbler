import math

import flask_login
from flask import Blueprint, render_template

from app.usecase.post_interactor import PostInteractor

bp = Blueprint("index", __name__)
post_interactor = PostInteractor()

page_number = 1
posts_per_page = 50


def get_posts_data(page_number):
    total_posts = post_interactor.get_total_post_count()
    total_pages = math.ceil(total_posts / posts_per_page)
    posts = post_interactor.get_posts_by_page(page_number, posts_per_page)
    data = {
        "posts": posts,
        "current_page": page_number,
        "total_pages": total_pages,
    }
    return data


@bp.route("/")
@flask_login.login_required
def home():
    page_number = 1
    data = get_posts_data(page_number)
    return render_template("index.html", data=data)


@bp.route("/page/<int:page_number>")
@flask_login.login_required
def page(page_number):
    data = get_posts_data(page_number)
    return render_template("index.html", data=data)
