from flask import Blueprint, request

from app.usecase.post_interactor import PostInteractor

bp = Blueprint("post", __name__)
post_interactor = PostInteractor()


@bp.route("/post", methods=["POST"])
def send():
    content = request.json.get("content")
    if content:
        post_interactor.create_post(content)

        return {"message": "投稿が成功しました"}
    else:
        return {"message": "投稿内容が空です"}, 400


@bp.route("/post/<post_id>", methods=["DELETE"])
def delete(post_id):
    res = post_interactor.delete_post(post_id)
    if res:
        return {"message": "投稿を削除しました"}
    else:
        return {"message": "投稿の削除に失敗しました"}, 404
