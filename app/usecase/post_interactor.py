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

    def get_posts_by_page(self, page_number, posts_per_page):
        post_repository = PostRepository()
        return post_repository.find_by_page(page_number, posts_per_page)

    def get_total_post_count(self):
        post_repository = PostRepository()
        return post_repository.get_total_post_count()
