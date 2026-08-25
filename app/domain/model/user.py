"""
[domain] ユーザーエンティティ

概要:
  アプリケーションの利用者を表すドメインモデル。
  表示名・メールアドレス・アバター画像を保持する。

  is_authenticated / is_active / is_anonymous / get_id は、
  ログインセッション管理が利用者オブジェクトに要求するインタフェース。
  domain層を特定のフレームワークに依存させないため、
  ライブラリのMixinを継承せず素のプロパティとして実装している。
"""

DEFAULT_AVATAR = "/static/images/bird_aoitori_bluebird.png"


class User:
    def __init__(self, id, username=None, password=None, avatar=None, email=None):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.avatar = avatar or DEFAULT_AVATAR

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
