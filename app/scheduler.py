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


def generate_weekly(app):
    with app.app_context():
        from app.usecase.summary_interactor import SummaryInteractor
        logger.info("Running scheduled weekly summary generation")
        try:
            interactor = SummaryInteractor()
            interactor.generate_weekly_summary()
        except Exception as e:
            logger.error(f"Scheduled weekly summary failed: {e}")


def generate_monthly(app):
    with app.app_context():
        from app.usecase.summary_interactor import SummaryInteractor
        logger.info("Running scheduled monthly summary generation")
        try:
            interactor = SummaryInteractor()
            interactor.generate_monthly_summary()
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
    )

    scheduler.start()
    logger.info("APScheduler started: weekly (Sun 23:00 UTC), monthly (last day 23:30 UTC)")
