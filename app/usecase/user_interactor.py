import logging

from flask_bcrypt import check_password_hash

from app.infrastructure.user_repository import UserRepository


# インタラクタ内での例外クラスの定義
class UserAlreadyExistsError(Exception):
    pass


class UserInteractor:
    def register_user(self, user):
        user_repository = UserRepository()
        existing_user = user_repository.already_register_user(user)
        if existing_user:
            raise UserAlreadyExistsError("アカウント名は既に使用されています")
        user_repository.save(user)

    def authenticate(self, username, password):
        user_repository = UserRepository()
        user = user_repository.find_by_username(username)
        if user and check_password_hash(user.password, password):
            logging.info('認証成功')
            return user
        return None
