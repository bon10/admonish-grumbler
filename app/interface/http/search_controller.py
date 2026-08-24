"""
[interface] 検索コントローラ

概要:
  投稿の全文検索機能を提供するFlask Blueprint。
  GET /search でキーワード検索を行い、結果をページ表示する。
  検索実行時に検索履歴を保存する。
"""

from flask import Blueprint, render_template, request

from app.infrastructure.post_repository import PostRepository
from app.infrastructure.search_history_repository import SearchHistoryRepository

bp = Blueprint("search", __name__)


@bp.route("/search")
def index():
    query = request.args.get("q", "").strip()
    results = []

    if query:
        search_history_repo = SearchHistoryRepository()
        search_history_repo.save(query)
        search_history_repo.delete_expired()

        post_repo = PostRepository()
        results = post_repo.search_by_keyword(query)

    return render_template("search.html", query=query, results=results)
