from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username=None, password=None, avatar=None):
        self.id = id
        self.username = username
        self.password = password
        if avatar:
            self.avatar = avatar
        else:
            self.avatar = "/static/images/bird_aoitori_bluebird.png"

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id
