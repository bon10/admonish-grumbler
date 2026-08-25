"""
本番デプロイ用のエントリーポイント。

デプロイ先(Vercel)は wsgi.py のトップレベル変数 `app` を
WSGIアプリケーションとして読み込む。
ローカル開発用の起動は run.py を参照。
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# create_app()内のログが取りこぼされないよう、アプリ生成より先にlogging設定を行う
logging.basicConfig(level=logging.DEBUG if os.environ.get("FLASK_DEBUG") == "true" else logging.INFO)

from app import create_app  # noqa: E402

app = create_app()
