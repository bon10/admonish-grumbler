"""
[infrastructure] サマリーリポジトリ

概要:
  SummaryエンティティのMongoDB永続化を担当する。
  サマリーの保存・全件取得・ID検索・タイプ別検索・
  サマリー更新・フィードバック更新・期間重複チェックを提供する。
"""
from datetime import datetime

from bson import ObjectId
from flask import current_app

from app.domain.model.summary import Summary


class SummaryRepository:
    def __init__(self):
        self.collection = current_app.mongo.summaries

    def _to_model(self, data):
        return Summary(
            id=str(data["_id"]),
            type=data["type"],
            period_start=data["period_start"],
            period_end=data["period_end"],
            post_count=data.get("post_count", 0),
            stress_score=data.get("stress_score", 0),
            happiness_score=data.get("happiness_score", 0),
            sentiment_score=data.get("sentiment_score", 0.0),
            emoji_expression=data.get("emoji_expression", ""),
            top_topics=data.get("top_topics", []),
            content_analysis=data.get("content_analysis", ""),
            advice=data.get("advice", ""),
            encouragement=data.get("encouragement", ""),
            scores_history=data.get("scores_history", []),
            feedback=data.get("feedback"),
            feedback_at=data.get("feedback_at"),
            status=data.get("status", "completed"),
            created_at=data.get("created_at"),
        )

    def _to_dict(self, summary):
        return {
            "type": summary.type,
            "period_start": summary.period_start,
            "period_end": summary.period_end,
            "post_count": summary.post_count,
            "stress_score": summary.stress_score,
            "happiness_score": summary.happiness_score,
            "sentiment_score": summary.sentiment_score,
            "emoji_expression": summary.emoji_expression,
            "top_topics": summary.top_topics,
            "content_analysis": summary.content_analysis,
            "advice": summary.advice,
            "encouragement": summary.encouragement,
            "scores_history": summary.scores_history,
            "feedback": summary.feedback,
            "feedback_at": summary.feedback_at,
            "status": summary.status,
            "created_at": summary.created_at or datetime.now(),
        }

    def save(self, summary):
        data = self._to_dict(summary)
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def find_all(self):
        data_list = self.collection.find().sort("period_end", -1)
        return [self._to_model(d) for d in data_list]

    def find_by_id(self, summary_id):
        data = self.collection.find_one({"_id": ObjectId(summary_id)})
        if data:
            return self._to_model(data)
        return None

    def find_by_type(self, summary_type):
        data_list = self.collection.find({"type": summary_type}).sort("period_end", -1)
        return [self._to_model(d) for d in data_list]

    def update_summary(self, summary_id, data_dict):
        self.collection.update_one(
            {"_id": ObjectId(summary_id)},
            {"$set": data_dict},
        )

    def update_feedback(self, summary_id, feedback):
        self.collection.update_one(
            {"_id": ObjectId(summary_id)},
            {"$set": {"feedback": feedback, "feedback_at": datetime.now()}},
        )

    def exists_for_period(self, summary_type, period_start, period_end):
        count = self.collection.count_documents({
            "type": summary_type,
            "period_start": period_start,
            "period_end": period_end,
            "status": "completed",
        })
        return count > 0
