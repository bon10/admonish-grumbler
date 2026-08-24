"""
[infrastructure] 定期サマリー生成スケジューラ

概要:
  APSchedulerを使い、週次(毎週日曜23:00 UTC)・月次(月末23:30 UTC)で
  SummaryInteractorを呼び出し、AI要約を自動生成するジョブを管理する。
"""

import logging

from flask_apscheduler import APScheduler

logger = logging.getLogger(__name__)
scheduler = APScheduler()


def _send_summary_emails(summary_id):
    """サマリー生成完了後、メールアドレス登録済みの全ユーザーに結果を送信する"""
    try:
        from app.infrastructure.email_client import EmailClient
        from app.infrastructure.summary_repository import SummaryRepository
        from app.infrastructure.user_repository import UserRepository

        summary_repo = SummaryRepository()
        summary = summary_repo.find_by_id(summary_id)
        if not summary:
            logger.warning(f"Summary {summary_id} not found, skipping email")
            return

        user_repo = UserRepository()
        users_with_email = user_repo.find_all_with_email()
        if not users_with_email:
            logger.info("No users with email registered, skipping email send")
            return

        email_client = EmailClient()
        sent_count = 0
        for user in users_with_email:
            if email_client.send_summary_email(user.email, summary):
                sent_count += 1

        logger.info(f"Summary emails sent: {sent_count}/{len(users_with_email)}")
    except Exception as e:
        logger.error(f"Failed to send summary emails: {e}")


def generate_weekly(app):
    with app.app_context():
        from app.usecase.summary_interactor import SummaryInteractor

        logger.info("Running scheduled weekly summary generation")
        try:
            interactor = SummaryInteractor()
            summary_id = interactor.generate_weekly_summary()
            if summary_id:
                _send_summary_emails(summary_id)
        except Exception as e:
            logger.error(f"Scheduled weekly summary failed: {e}")


def generate_monthly(app):
    with app.app_context():
        from app.usecase.summary_interactor import SummaryInteractor

        logger.info("Running scheduled monthly summary generation")
        try:
            interactor = SummaryInteractor()
            summary_id = interactor.generate_monthly_summary()
            if summary_id:
                _send_summary_emails(summary_id)
        except Exception as e:
            logger.error(f"Scheduled monthly summary failed: {e}")


def init_scheduler(app):
    scheduler.init_app(app)

    # Weekly: every Sunday at 23:00 UTC
    scheduler.add_job(
        id="weekly_summary",
        func=generate_weekly,
        args=[app],
        trigger="cron",
        day_of_week="sun",
        hour=23,
        minute=0,
        misfire_grace_time=None,
        coalesce=True,
    )

    # Monthly: last day of month at 23:30 UTC
    scheduler.add_job(
        id="monthly_summary",
        func=generate_monthly,
        args=[app],
        trigger="cron",
        day="last",
        hour=23,
        minute=30,
        misfire_grace_time=None,
        coalesce=True,
    )

    scheduler.start()
    logger.info("APScheduler started: weekly (Sun 23:00 UTC), monthly (last day 23:30 UTC)")
