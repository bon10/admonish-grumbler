"""
[infrastructure] ローカル環境用の定期実行スケジューラ

概要:
  週次・月次サマリーをアプリのプロセス内で定期実行する。
  ENABLE_IN_PROCESS_SCHEDULERがtrueのときだけ起動する。

  本番(Vercel)はリクエスト単位で関数が起動し常駐プロセスを持てないため、
  そちらではVercel Cronがcron_controllerのエンドポイントを叩いて生成する。
  このスケジューラは、常駐プロセスを持てるローカル環境で同じ定期実行を再現するためのもの。

  呼び先はcron_controllerと同じgenerate_scheduled_summaryなので、
  生成処理も重複起動の抑止も、ローカルと本番で同じ経路を通る。

  発火時刻はvercel.jsonのcron定義から読み出す。
  ローカルと本番で時刻を二重管理するとどちらかを直し忘れてズレるため、
  本番の設定ファイルを唯一の出所にしている。
"""

import json
import logging
import os
import re
from pathlib import Path

from apscheduler.triggers.cron import CronTrigger
from flask_apscheduler import APScheduler

logger = logging.getLogger(__name__)
scheduler = APScheduler()

VERCEL_CONFIG_PATH = Path(__file__).resolve().parent.parent / "vercel.json"

# cronのpath末尾がそのままサマリー種別になる(/api/cron/summary/weekly -> weekly)
SUPPORTED_SUMMARY_TYPES = ("weekly", "monthly")

# crontabの曜日番号の並び(0が日曜)
CRONTAB_DAY_NAMES = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")


def _to_apscheduler_day_of_week(field):
    """
    crontab表記の曜日(0-6が日〜土、7も日曜)をAPSchedulerの曜日名に置き換える。

    APSchedulerは数字の曜日を0=月曜として解釈するため、
    Vercelのcron式をそのまま渡すと発火日が1日ずれる。
    """
    return re.sub(r"\d+", lambda m: CRONTAB_DAY_NAMES[int(m.group()) % 7], field)


def _to_trigger(expression):
    """Vercelのcron式(分 時 日 月 曜)をAPSchedulerのトリガーに変換する"""
    minute, hour, day, month, day_of_week = expression.split()
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=_to_apscheduler_day_of_week(day_of_week),
        # Vercel Cronは常にUTCで解釈するため、ローカルの時刻設定に引きずられないよう明示する
        timezone="UTC",
    )


def is_enabled():
    return os.getenv("ENABLE_IN_PROCESS_SCHEDULER", "").lower() == "true"


def load_schedules():
    """vercel.jsonのcron定義から (サマリー種別, cron式) の一覧を読み出す"""
    with VERCEL_CONFIG_PATH.open(encoding="utf-8") as f:
        crons = json.load(f).get("crons", [])

    schedules = []
    for entry in crons:
        path = entry.get("path", "")
        summary_type = path.rsplit("/", 1)[-1]
        if summary_type not in SUPPORTED_SUMMARY_TYPES:
            logger.warning(f"Unsupported cron path, skipping: {path}")
            continue
        schedules.append((summary_type, entry["schedule"]))

    return schedules


def _generate(app, summary_type):
    with app.app_context():
        from app.usecase.summary_interactor import SummaryInteractor

        try:
            executed, summary_id = SummaryInteractor().generate_scheduled_summary(summary_type)
            logger.info(f"Scheduled {summary_type} summary: executed={executed}, id={summary_id}")
        except Exception as e:
            logger.error(f"Scheduled {summary_type} summary failed: {e}")


def init_scheduler(app):
    try:
        schedules = load_schedules()
    except Exception as e:
        # 定期実行が動かないだけで画面は使えるため、アプリの起動自体は止めない
        logger.error(f"Failed to load cron schedules from {VERCEL_CONFIG_PATH}: {e}")
        return

    scheduler.init_app(app)

    for summary_type, expression in schedules:
        scheduler.add_job(
            id=f"{summary_type}_summary",
            func=_generate,
            args=[app, summary_type],
            trigger=_to_trigger(expression),
            misfire_grace_time=None,
            coalesce=True,
        )
        logger.info(f"Scheduled {summary_type} summary: '{expression}' (UTC)")

    scheduler.start()
