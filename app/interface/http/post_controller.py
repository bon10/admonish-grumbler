from flask import Blueprint, request

from app import socketio
from app.usecase.post_interactor import PostInteractor

bp = Blueprint('post', __name__)
post_interactor = PostInteractor()


@bp.route('/post', methods=['POST'])
def send():
    content = request.json.get('content')
    if content:
        post = post_interactor.create_post(content)
        # 新しいメッセージをブロードキャスト
        socketio.emit('new_message', post.to_dict())

        return {'message': '投稿が成功しました'}
    else:
        return {'message': '投稿内容が空です'}, 400
