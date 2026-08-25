"""
[usecase] ユーザーユースケース

概要:
  利用者の認証に関するアプリケーションロジックを制御する。
  本アプリの利用者は管理ユーザー1人だけのため登録処理は持たず、
  環境変数に設定された資格情報との照合と、セッションからの利用者復元のみを提供する。
"""

from app.infrastructure.admin_credentials import load_admin_user, verify_password


class UserInteractor:
    def authenticate(self, username, password):
        """資格情報を照合し、一致すればUserを、一致しなければNoneを返す"""
        return verify_password(username, password)

    def find_login_user(self, user_id):
        """セッションに保存された利用者IDから、ログイン中のUserを復元する"""
        admin = load_admin_user()
        if admin and admin.get_id() == user_id:
            return admin
        return None
