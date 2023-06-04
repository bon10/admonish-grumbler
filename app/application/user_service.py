from app.domain.model.user import User
from app.infrastructure.mongoengine_repository import UserRepository
from app.infrastructure.security import verify_password


class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register_user(self, username, password):
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise ValueError('Username already exists')

        user = User(username=username, password=password)
        self.user_repository.create(user)

    def authenticate_user(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None

