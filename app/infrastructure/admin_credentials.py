"""
[infrastructure] 管理ユーザーの資格情報

概要:
  本アプリの利用者は管理ユーザー1人だけであり、ユーザー登録機能を持たない。
  そのため資格情報はDBではなく環境変数(ADMIN_USERNAME / ADMIN_PASSWORD_HASH)を
  唯一の出所とする。ADMIN_PASSWORD_HASHにはbcryptハッシュを設定する。
"""

import logging
import os

from flask_bcrypt import check_password_hash

from app.domain.model.user import User

logger = logging.getLogger(__name__)


def load_admin_user():
    """環境変数から管理ユーザーを組み立てる。ADMIN_USERNAMEが未設定ならNoneを返す。"""
    username = os.getenv("ADMIN_USERNAME")
    if not username:
        return None
    return User(id=username, username=username)


def verify_password(username, password):
    """
    入力された資格情報を管理ユーザーのものと照合し、一致すればUserを、しなければNoneを返す。

    ADMIN_USERNAMEとADMIN_PASSWORD_HASHのいずれかが未設定の環境では、
    誰もログインできない状態を正とする。設定漏れのまま全員が素通りする事故を防ぐため。
    """
    expected_username = os.getenv("ADMIN_USERNAME")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    if not expected_username or not password_hash:
        logger.error("ADMIN_USERNAME または ADMIN_PASSWORD_HASH が未設定のため、ログインを受け付けない")
        return None

    if username != expected_username:
        return None

    if not check_password_hash(password_hash, password):
        return None

    return User(id=expected_username, username=expected_username)
