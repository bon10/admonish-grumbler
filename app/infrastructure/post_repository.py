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
        self.post.insert_one(post_data)

    def find_all(self):
        post_data = self.post.find()
        posts = []
        for data in post_data:
            post = Post(
                content=data['content'],
                timestamp=data['timestamp']
            )
            posts.append(post)
        return posts
