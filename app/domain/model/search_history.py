"""
[domain] 検索履歴エンティティ

概要:
  ユーザーの検索クエリを表すドメインモデル。
  検索語(query)、検索日時(searched_at)、識別子(id)を保持する。
"""


class SearchHistory:
    def __init__(self, query, searched_at, id=None):
        self.id = id
        self.query = query
        self.searched_at = searched_at
