from app.infrastructure.post_repository import PostRepository


class PostInteractor:
    def create_post(self, content):
        post_repository = PostRepository()
        post_repository.save(content)

    def get_all_posts(self):
        post_repository = PostRepository()
        return post_repository.find_all()

