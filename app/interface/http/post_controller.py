"""
[interface] 投稿APIコントローラ

概要:
  投稿(Post)に関するHTTPエンドポイントを定義するFlask Blueprint。
  POST /post(新規投稿)、PUT /post/<id>(更新)、DELETE /post/<id>(削除)を提供する。
  リクエストの受け取りとレスポンスの返却のみを担当し、ビジネスロジックはPostInteractorに委譲する。
"""
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


@bp.route("/post/<post_id>", methods=["PUT"])
def update(post_id):
    content = request.json.get("content")
    if not content:
        return {"message": "投稿内容が空です"}, 400
    res = post_interactor.update_post(post_id, content)
    if res:
        return {"message": "投稿を更新しました"}
    else:
        return {"message": "投稿の更新に失敗しました"}, 404


@bp.route("/post/<post_id>", methods=["DELETE"])
def delete(post_id):
    res = post_interactor.delete_post(post_id)
    if res:
        return {"message": "投稿を削除しました"}
    else:
        return {"message": "投稿の削除に失敗しました"}, 404
