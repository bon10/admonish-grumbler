"""
[infrastructure] フィードバックプロファイルリポジトリ

概要:
  FeedbackProfileエンティティのMongoDB永続化を担当する。
  プロファイルはアプリ全体で1件のみのため、固定IDの単一ドキュメントとして扱う。
  未正規化フィードバックの追加・読み出し・正規化結果の保存・
  1回きりの指示の削除を提供する。
"""

from datetime import datetime

from flask import current_app

from app.domain.model.feedback_profile import (
    FeedbackInstruction,
    FeedbackPendingItem,
    FeedbackProfile,
)

# プロファイルはアプリ全体で1件のみ存在するため、固定のドキュメントIDを使う
PROFILE_ID = "default"


class FeedbackProfileRepository:
    def __init__(self):
        self.collection = current_app.mongo.feedback_profile

    def load(self):
        data = self.collection.find_one({"_id": PROFILE_ID})
        if not data:
            return FeedbackProfile()
        return FeedbackProfile(
            instructions=[_to_instruction(d) for d in data.get("instructions", [])],
            pending=[_to_pending(d) for d in data.get("pending", [])],
            updated_at=data.get("updated_at"),
        )

    def add_pending(self, text, summary_id=None):
        """
        生フィードバックを未正規化キューへ積む。

        フィードバック投稿(リクエストスレッド)とサマリー生成(バックグラウンドスレッド)が
        同時にプロファイルへ書き込みうるため、read-modify-writeを避けて$pushで追加する。
        """
        item = FeedbackPendingItem(text=text, summary_id=summary_id)
        self.collection.update_one(
            {"_id": PROFILE_ID},
            {
                "$push": {"pending": _from_pending(item)},
                "$set": {"updated_at": datetime.now()},
                "$setOnInsert": {"instructions": []},
            },
            upsert=True,
        )
        return item.id

    def save_instructions(self, instructions, consumed_pending_ids):
        """正規化後の指示リストで置き換え、正規化に使った未正規化フィードバックを取り除く"""
        self.collection.update_one(
            {"_id": PROFILE_ID},
            {
                "$set": {
                    "instructions": [_from_instruction(i) for i in instructions],
                    "updated_at": datetime.now(),
                },
                "$pull": {"pending": {"id": {"$in": list(consumed_pending_ids)}}},
            },
            upsert=True,
        )

    def remove_instructions(self, instruction_ids):
        """指定IDの指示を取り除く。1回きりの指示を生成後に破棄する用途で使う。"""
        if not instruction_ids:
            return
        self.collection.update_one(
            {"_id": PROFILE_ID},
            {
                "$pull": {"instructions": {"id": {"$in": list(instruction_ids)}}},
                "$set": {"updated_at": datetime.now()},
            },
        )


def _to_instruction(data):
    return FeedbackInstruction(
        id=data.get("id"),
        text=data.get("text", ""),
        category=data.get("category"),
        scope=data.get("scope"),
        persistent=data.get("persistent", True),
        weight=data.get("weight", 1),
        created_at=data.get("created_at"),
        last_reinforced_at=data.get("last_reinforced_at"),
    )


def _from_instruction(instruction):
    return {
        "id": instruction.id,
        "text": instruction.text,
        "category": instruction.category,
        "scope": instruction.scope,
        "persistent": instruction.persistent,
        "weight": instruction.weight,
        "created_at": instruction.created_at,
        "last_reinforced_at": instruction.last_reinforced_at,
    }


def _to_pending(data):
    return FeedbackPendingItem(
        id=data.get("id"),
        text=data.get("text", ""),
        summary_id=data.get("summary_id"),
        created_at=data.get("created_at"),
    )


def _from_pending(item):
    return {
        "id": item.id,
        "text": item.text,
        "summary_id": item.summary_id,
        "created_at": item.created_at,
    }
