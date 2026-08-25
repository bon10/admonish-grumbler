"""
ADMIN_PASSWORD_HASH に設定する bcrypt ハッシュを生成する。

使い方:
    python scripts/generate_password_hash.py

パスワードは引数ではなく対話入力で受け取る。
コマンド履歴やプロセス一覧に平文が残るのを避けるため。
"""

import getpass
import sys

from flask_bcrypt import Bcrypt


def main():
    password = getpass.getpass("パスワード: ")
    if not password:
        print("パスワードが空です", file=sys.stderr)
        return 1
    if password != getpass.getpass("パスワード(確認): "):
        print("パスワードが一致しません", file=sys.stderr)
        return 1

    print()
    print("以下を .env と Vercel の環境変数に設定してください:")
    print(f'ADMIN_PASSWORD_HASH="{Bcrypt().generate_password_hash(password).decode()}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
