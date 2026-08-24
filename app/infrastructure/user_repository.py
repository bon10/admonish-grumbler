"""
[infrastructure] ユーザーリポジトリ

概要:
  UserエンティティのMongoDB永続化を担当する。
  ユーザーの保存・ユーザー名による検索・重複チェックを提供する。
"""

import logging

from flask import current_app

from app.domain.model.user import User


class UserRepository:

    def __init__(self):
        self.collection = current_app.mongo.users

    def already_register_user(self, user):
        existing_user = self.collection.find_one({"username": user.username})
        return existing_user

    def save(self, user):
        user_data = {
            "username": user.username,
            "password": user.password,
            "avatar": user.avatar,
            "email": user.email,
        }
        self.collection.insert_one(user_data)

    def find_by_username(self, username):
        user_data = self.collection.find_one({"username": username})
        logging.info(user_data)
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
