from app.domain.model.user import User
from app.infrastructure.user_repository import UserRepository


class UserInteractor:
    def __init__(self):
        self.user_repository = UserRepository()

    def register_user(self, user):
        self.user_repository.save(user)

    def authenticate(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user and check_password_hash(user.password, password):
            return user
        return None