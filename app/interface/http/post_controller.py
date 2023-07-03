from flask import Blueprint, request

from app.usecase.post_interactor import PostInteractor

bp = Blueprint('post', __name__)
post_interactor = PostInteractor()


@bp.route('/post', methods=['POST'])
def send():
    content = request.json.get('content')
    if content:
        post_interactor.create_post(content)

        return {'message': '投稿が成功しました'}
    else:
        return {'message': '投稿内容が空です'}, 400
