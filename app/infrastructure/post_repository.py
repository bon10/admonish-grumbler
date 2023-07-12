from datetime import datetime

from flask import current_app

from app.domain.model.post import Post


class PostRepository:
    def __init__(self):
        self.post = current_app.mongo.posts

    def save(self, content):
        timestamp = datetime.now()
        post_data = {
            'content': content,
            'timestamp': timestamp
        }
        return self.post.insert_one(post_data)

    def find_all(self):
        post_data = self.post.find().sort('timestamp', -1)
        posts = []
        for data in post_data:
            post = Post(
                content=data['content'],
                timestamp=data['timestamp']
            )
            posts.append(post)
        return posts

    def find_by_page(self, page_number, posts_per_page):
        post_data = self.post.find().sort('timestamp', -1).skip(
            posts_per_page * (page_number - 1)).limit(posts_per_page)
        posts = []
        for data in post_data:
            post = Post(
                content=data['content'],
                timestamp=data['timestamp']
            )
            posts.append(post)
        return posts

    def get_total_post_count(self):
        count = self.post.count_documents({})
        return count
