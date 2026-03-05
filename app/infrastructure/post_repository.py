"""
[infrastructure] 投稿リポジトリ

概要:
  PostエンティティのMongoDB永続化を担当する。
  投稿の保存・全件取得・ページネーション取得・日付範囲検索・
  ID検索・更新・削除の各CRUD操作を提供する。
"""
from datetime import datetime

from bson import ObjectId
from flask import current_app

from app.domain.model.post import Post


class PostRepository:
    def __init__(self):
        self.post = current_app.mongo.posts

    def save(self, content):
        timestamp = datetime.now()
        post_data = {"content": content, "timestamp": timestamp}
        return self.post.insert_one(post_data)

    def find_all(self):
        post_data = self.post.find().sort("timestamp", -1)
        posts = []
        for data in post_data:
            post = Post(content=data["content"], timestamp=data["timestamp"])
            posts.append(post)
        return posts

    def find_by_page(self, page_number, posts_per_page):
        post_data = (
            self.post.find().sort("timestamp", -1).skip(posts_per_page * (page_number - 1)).limit(posts_per_page)
        )
        posts = []
        for data in post_data:
            post = Post(content=data["content"], timestamp=data["timestamp"], id=str(data["_id"]))
            posts.append(post)
        return posts

    def get_total_post_count(self):
        count = self.post.count_documents({})
        return count

    def find_by_date_range(self, start, end):
        post_data = self.post.find({
            "timestamp": {"$gte": start, "$lte": end}
        }).sort("timestamp", 1)
        posts = []
        for data in post_data:
            post = Post(content=data["content"], timestamp=data["timestamp"], id=str(data["_id"]))
            posts.append(post)
        return posts

    def find_by_id(self, id):
        data = self.post.find_one({"_id": ObjectId(id)})
        if data:
            return Post(content=data["content"], timestamp=data["timestamp"], id=str(data["_id"]))
        return None

    def update_by_id(self, id, content):
        result = self.post.update_one({"_id": ObjectId(id)}, {"$set": {"content": content}})
        return result.modified_count > 0

    def delete_by_id(self, id):
        """
        指定されたIDのポストを削除します。
        :param id: 削除したいポストのID
        :return: 削除操作の結果
        """
        result = self.post.delete_one({"_id": ObjectId(id)})
        return result
