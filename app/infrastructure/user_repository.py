"""
[infrastructure] ユーザーリポジトリ

概要:
  UserエンティティのMongoDB永続化を担当する。
  ユーザー名による検索と、サマリー送信先メールアドレスの参照・更新を提供する。
  資格情報は環境変数を出所とするためこのリポジトリでは扱わない(admin_credentialsを参照)。
"""

from flask import current_app

from app.domain.model.user import User


class UserRepository:

    def __init__(self):
        self.collection = current_app.mongo.users

    def find_by_username(self, username):
        user_data = self.collection.find_one({"username": username})
        if user_data:
            user = User(
                id=user_data["_id"],
                username=user_data.get("username"),
                password=user_data.get("password"),
                avatar=user_data.get("avatar", ""),
                email=user_data.get("email", ""),
            )
            return user
        return None

    def find_all_with_email(self):
        """メールアドレスが登録されている全ユーザーを取得する"""
        users_data = self.collection.find({"email": {"$exists": True, "$nin": ["", None]}})
        return [
            User(
                id=u["_id"],
                username=u.get("username"),
                email=u.get("email", ""),
            )
            for u in users_data
        ]

    def update_email(self, username, email):
        """ユーザー名でメールアドレスを更新する"""
        self.collection.update_one(
            {"username": username},
            {"$set": {"email": email}},
            upsert=True,
        )
