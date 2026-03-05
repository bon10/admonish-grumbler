"""
[domain] ユーザー登録用の値オブジェクト

概要:
  新規ユーザー登録時に必要な情報(id, username, password_hash)を
  まとめて運ぶためのデータ転送オブジェクト。
"""


class RegisterUser:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
