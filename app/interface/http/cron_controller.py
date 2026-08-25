"""
[interface] 定期実行コントローラ

概要:
  週次・月次サマリーの定期生成を外部のcronから起動するためのFlask Blueprint。
  GET/POST /api/cron/summary/weekly、GET/POST /api/cron/summary/monthly を提供する。

  アプリプロセス内に常駐スケジューラを置く代わりにHTTPで起動する方式にしている。
  デプロイ先(Vercel)がリクエスト単位で関数を起動するため常駐プロセスを持てないため。

  このエンドポイントは画面のログインを経由しないため、
  CRON_SECRETと突き合わせるBearerトークンで呼び出し元を認証する。
"""

import hmac
import logging
import os

from flask import Blueprint, jsonify, request

from app.usecase.summary_interactor import SummaryInteractor

logger = logging.getLogger(__name__)

bp = Blueprint("cron", __name__, url_prefix="/api/cron")
summary_interactor = SummaryInteractor()


def _is_authorized():
    """
    リクエストが正規のcron起動かを判定する。

    CRON_SECRETが未設定の環境では誰も起動できない状態を正とする。
    公開エンドポイントなので、設定漏れのまま第三者にAI生成を叩かれる事故を防ぐため。
    """
    secret = os.getenv("CRON_SECRET")
    if not secret:
        logger.error("CRON_SECRET が未設定のため、定期実行の呼び出しを受け付けない")
        return False

    # 突き合わせの所要時間からシークレットが推測されないよう定数時間で比較する
    return hmac.compare_digest(request.headers.get("Authorization", ""), f"Bearer {secret}")


def _run(summary_type):
    if not _is_authorized():
        return jsonify({"error": "unauthorized"}), 401

    executed, summary_id = summary_interactor.generate_scheduled_summary(summary_type)
    if not executed:
        return jsonify({"status": "skipped", "reason": "recently_generated"})

    return jsonify({"status": "generated", "summary_id": summary_id})


@bp.route("/summary/weekly", methods=["GET", "POST"])
def weekly():
    return _run("weekly")


@bp.route("/summary/monthly", methods=["GET", "POST"])
def monthly():
    return _run("monthly")
