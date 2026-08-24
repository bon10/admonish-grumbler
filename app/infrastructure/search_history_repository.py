"""
[infrastructure] 検索履歴リポジトリ

概要:
  SearchHistoryエンティティのMongoDB永続化を担当する。
  検索履歴の保存・期間検索・60日超の古い履歴の自動削除を提供する。
"""

from datetime import datetime, timedelta

from flask import current_app

from app.domain.model.search_history import SearchHistory

RETENTION_DAYS = 60


class SearchHistoryRepository:
    def __init__(self):
        self.collection = current_app.mongo.search_histories

    def save(self, query):
        self.collection.insert_one(
            {
                "query": query,
                "searched_at": datetime.now(),
            }
        )

    def find_by_date_range(self, start, end):
        data_list = self.collection.find({"searched_at": {"$gte": start, "$lte": end}}).sort("searched_at", -1)
        return [self._to_model(d) for d in data_list]

    def delete_expired(self):
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        result = self.collection.delete_many({"searched_at": {"$lt": cutoff}})
        return result.deleted_count

    def _to_model(self, data):
        return SearchHistory(
            id=str(data["_id"]),
            query=data["query"],
            searched_at=data["searched_at"],
        )
