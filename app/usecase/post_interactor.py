import logging

from app.infrastructure.post_repository import PostRepository


class PostInteractor:
    def create_post(self, content):
        post_repository = PostRepository()
        post = post_repository.save(content)
        logging.info(f'New post created: {post}')
        return post

    def get_all_posts(self):
        post_repository = PostRepository()
        return post_repository.find_all()
