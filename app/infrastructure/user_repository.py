import logging

from flask import current_app

from app.domain.model.user import User


class UserRepository:

    def __init__(self):
        self.collection = current_app.mongo.users

    def already_register_user(self, user):
        existing_user = self.collection.find_one(
            {'username': user.username})
        return existing_user

    def save(self, user):
        user_data = {
            'username': user.username,
            'password': user.password,
            'avatar': user.avatar,
        }
        self.collection.insert_one(user_data)

    def find_by_username(self, username):
        user_data = self.collection.find_one({'username': username})
        logging.info(user_data)
        if user_data:
            user = User(
                id=user_data['_id'],
                username=user_data.get('username'),
                password=user_data.get('password'),
                avatar=user_data.get('avatar', ''),
            )
            return user
        return None
