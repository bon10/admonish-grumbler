"""
[usecase] サマリーユースケース

概要:
  AI要約(Summary)の生成・取得・フィードバック保存に関するアプリケーションロジックを制御する。
  週次・月次サマリーの非同期生成(start → run_generation)と、
  スケジューラ用の同期生成(generate_weekly/monthly_summary)の両方を提供する。
  投稿をプレーンテキストに変換し、AIClientで分析、結果をSummaryRepositoryに保存する。
"""
import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from app.infrastructure.ai_client import AIClient
from app.infrastructure.post_repository import PostRepository
from app.infrastructure.summary_repository import SummaryRepository
from app.domain.model.summary import Summary

logger = logging.getLogger(__name__)


def html_to_plain_text(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


class SummaryInteractor:
    def get_all_summaries(self):
        repo = SummaryRepository()
        return repo.find_all()

    def get_summary_by_id(self, summary_id):
        repo = SummaryRepository()
        return repo.find_by_id(summary_id)

    def get_summary_status(self, summary_id):
        repo = SummaryRepository()
        summary = repo.find_by_id(summary_id)
        if not summary:
            return None
        return summary.status

    def save_feedback(self, summary_id, feedback):
        repo = SummaryRepository()
        repo.update_feedback(summary_id, feedback)

    def start_weekly_summary(self):
        now = datetime.now()
        period_end = now
        period_start = now - timedelta(days=7)
        period_label = f"{period_start.strftime('%Y/%m/%d')}〜{period_end.strftime('%Y/%m/%d')}の1週間"
        return self._start_summary("weekly", period_start, period_end, period_label)

    def start_monthly_summary(self):
        now = datetime.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        period_label = f"{period_start.strftime('%Y年%m月')}の1ヶ月間"
        return self._start_summary("monthly", period_start, period_end, period_label)

    def _start_summary(self, summary_type, period_start, period_end, period_label):
        """Save a placeholder summary with status='generating' and return its id."""
        summary_repo = SummaryRepository()
        summary = Summary(
            type=summary_type,
            period_start=period_start,
            period_end=period_end,
            post_count=0,
            status="generating",
        )
        summary_id = summary_repo.save(summary)
        return summary_id, summary_type, period_start, period_end, period_label

    def run_generation(self, summary_id, summary_type, period_start, period_end, period_label):
        """Run AI generation (called from background thread with app context)."""
        post_repo = PostRepository()
        summary_repo = SummaryRepository()

        posts = post_repo.find_by_date_range(period_start, period_end)

        if not posts:
            logger.info(f"No posts found for {summary_type} summary ({period_start} - {period_end})")
            summary_repo.update_summary(summary_id, {
                "status": "failed",
                "content_analysis": "この期間には投稿がありませんでした。",
            })
            return

        # Convert posts to plain text
        posts_text = ""
        for i, post in enumerate(posts, 1):
            plain = html_to_plain_text(post.content)
            timestamp = post.timestamp.strftime("%Y/%m/%d %H:%M")
            posts_text += f"{i}. [{timestamp}] {plain}\n"

        # Get previous feedback for prompt injection
        previous_feedback = None
        latest = summary_repo.find_latest_by_type(summary_type)
        if latest and latest.feedback:
            previous_feedback = latest.feedback

        # Build scores history from past summaries
        past_summaries = summary_repo.find_by_type(summary_type)
        scores_history = []
        for s in reversed(past_summaries):
            if s.status == "completed":
                scores_history.append({
                    "date": s.period_end.strftime("%m/%d"),
                    "stress": s.stress_score,
                    "happiness": s.happiness_score,
                    "sentiment": s.sentiment_score,
                })
        # Keep last 12 data points for the trend chart
        scores_history = scores_history[-12:]

        try:
            ai_service = AIClient()
            result = ai_service.analyze_posts(posts_text, summary_type, period_label, previous_feedback)

            # Append current scores to history
            scores_history.append({
                "date": period_end.strftime("%m/%d"),
                "stress": result["stress_score"],
                "happiness": result["happiness_score"],
                "sentiment": result["sentiment_score"],
            })

            summary_repo.update_summary(summary_id, {
                "post_count": len(posts),
                "stress_score": result["stress_score"],
                "happiness_score": result["happiness_score"],
                "sentiment_score": result["sentiment_score"],
                "emoji_expression": result["emoji_expression"],
                "top_topics": result["top_topics"],
                "content_analysis": result["content_analysis"],
                "advice": result["advice"],
                "encouragement": result["encouragement"],
                "scores_history": scores_history,
                "status": "completed",
            })
            logger.info(f"{summary_type} summary generated: {summary_id}")

        except Exception as e:
            logger.error(f"Failed to generate {summary_type} summary: {e}")
            summary_repo.update_summary(summary_id, {
                "post_count": len(posts),
                "status": "failed",
                "content_analysis": f"サマリー生成中にエラーが発生しました: {str(e)}",
            })

    # Keep synchronous methods for scheduler compatibility
    def generate_weekly_summary(self):
        now = datetime.now()
        period_end = now
        period_start = now - timedelta(days=7)
        period_label = f"{period_start.strftime('%Y/%m/%d')}〜{period_end.strftime('%Y/%m/%d')}の1週間"
        return self._generate_summary("weekly", period_start, period_end, period_label)

    def generate_monthly_summary(self):
        now = datetime.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        period_label = f"{period_start.strftime('%Y年%m月')}の1ヶ月間"
        return self._generate_summary("monthly", period_start, period_end, period_label)

    def _generate_summary(self, summary_type, period_start, period_end, period_label):
        post_repo = PostRepository()
        summary_repo = SummaryRepository()

        posts = post_repo.find_by_date_range(period_start, period_end)

        if not posts:
            logger.info(f"No posts found for {summary_type} summary ({period_start} - {period_end})")
            summary = Summary(
                type=summary_type,
                period_start=period_start,
                period_end=period_end,
                post_count=0,
                status="failed",
                content_analysis="この期間には投稿がありませんでした。",
            )
            summary_repo.save(summary)
            return None

        # Convert posts to plain text
        posts_text = ""
        for i, post in enumerate(posts, 1):
            plain = html_to_plain_text(post.content)
            timestamp = post.timestamp.strftime("%Y/%m/%d %H:%M")
            posts_text += f"{i}. [{timestamp}] {plain}\n"

        # Get previous feedback for prompt injection
        previous_feedback = None
        latest = summary_repo.find_latest_by_type(summary_type)
        if latest and latest.feedback:
            previous_feedback = latest.feedback

        # Build scores history from past summaries
        past_summaries = summary_repo.find_by_type(summary_type)
        scores_history = []
        for s in reversed(past_summaries):
            if s.status == "completed":
                scores_history.append({
                    "date": s.period_end.strftime("%m/%d"),
                    "stress": s.stress_score,
                    "happiness": s.happiness_score,
                    "sentiment": s.sentiment_score,
                })
        # Keep last 12 data points for the trend chart
        scores_history = scores_history[-12:]

        try:
            ai_service = AIClient()
            result = ai_service.analyze_posts(posts_text, summary_type, period_label, previous_feedback)

            # Append current scores to history
            scores_history.append({
                "date": period_end.strftime("%m/%d"),
                "stress": result["stress_score"],
                "happiness": result["happiness_score"],
                "sentiment": result["sentiment_score"],
            })

            summary = Summary(
                type=summary_type,
                period_start=period_start,
                period_end=period_end,
                post_count=len(posts),
                stress_score=result["stress_score"],
                happiness_score=result["happiness_score"],
                sentiment_score=result["sentiment_score"],
                emoji_expression=result["emoji_expression"],
                top_topics=result["top_topics"],
                content_analysis=result["content_analysis"],
                advice=result["advice"],
                encouragement=result["encouragement"],
                scores_history=scores_history,
                status="completed",
            )
            summary_id = summary_repo.save(summary)
            logger.info(f"{summary_type} summary generated: {summary_id}")
            return summary_id

        except Exception as e:
            logger.error(f"Failed to generate {summary_type} summary: {e}")
            summary = Summary(
                type=summary_type,
                period_start=period_start,
                period_end=period_end,
                post_count=len(posts),
                status="failed",
                content_analysis=f"サマリー生成中にエラーが発生しました: {str(e)}",
            )
            summary_repo.save(summary)
            return None
