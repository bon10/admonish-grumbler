from app import mongo
from app.domain.model.user import User


class UserRepository:
    def save(self, user):
        user_data = {
            'username': user.username,
            'password': user.password
        }
        mongo.db.users.insert_one(user_data)

    def find_by_username(self, username):
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            user = User(
                username=user_data['username'],
                password=user_data['password']
            )
            return user
        return None