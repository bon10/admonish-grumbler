"""
[usecase] サマリーユースケース

概要:
  AI要約(Summary)の生成・取得・フィードバック保存に関するアプリケーションロジックを制御する。
  週次・月次サマリーの非同期生成(start → run_generation)と、
  スケジューラ用の同期生成(generate_weekly/monthly_summary)の両方を提供する。
  投稿をプレーンテキストに変換し、AIClientで分析、結果をSummaryRepositoryに保存する。
  ユーザーのフィードバックは指示リストへ正規化してFeedbackProfileに蓄積し、
  以降すべての分析へ継続的に注入する。
"""

import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from app.domain.model.feedback_profile import FeedbackInstruction, apply_limits
from app.domain.model.summary import Summary
from app.domain.services.feedback_prompt_builder import build_instructions_text
from app.infrastructure.ai_client import AIClient
from app.infrastructure.feedback_profile_repository import FeedbackProfileRepository
from app.infrastructure.post_repository import PostRepository
from app.infrastructure.search_history_repository import SearchHistoryRepository
from app.infrastructure.summary_repository import SummaryRepository

logger = logging.getLogger(__name__)

# 未正規化フィードバックがこの件数に達したら、生成を待たずに正規化を実行する
PENDING_CONSOLIDATION_THRESHOLD = 3


def html_to_plain_text(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _build_search_history_text(period_start, period_end):
    """該当期間の検索履歴をテキスト化する"""
    try:
        repo = SearchHistoryRepository()
        histories = repo.find_by_date_range(period_start, period_end)
        if not histories:
            return None
        lines = []
        for h in histories:
            lines.append(f"- [{h.searched_at.strftime('%m/%d %H:%M')}] {h.query}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Failed to fetch search history: {e}")
        return None


def _consolidate_feedback():
    """
    未正規化のフィードバックを既存の指示リストへ統合し、統合後のプロファイルを返す。

    AIが返した各指示のsource_idsをたどって統合元の言及回数・作成日時を引き継ぐことで、
    正規化を繰り返しても「ユーザーが何度求めたか」が失われないようにする。
    """
    repo = FeedbackProfileRepository()
    profile = repo.load()
    if not profile.pending:
        return profile

    try:
        merged = AIClient().merge_feedback(profile.instructions, [p.text for p in profile.pending])
    except Exception as e:
        # 正規化に失敗してもpendingは消さないため、次の生成時に再試行される
        logger.error(f"Failed to consolidate feedback: {e}")
        return profile

    existing_by_id = {i.id: i for i in profile.instructions}
    claimed_ids = set()
    now = datetime.now()
    instructions = []

    for item in merged:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        # 同じ既存指示が複数の出力に割り当てられてもIDが重複しないよう、先着順で引き当てる
        sources = []
        for source_id in item.get("source_ids", []):
            source = existing_by_id.get(source_id)
            if source and source_id not in claimed_ids:
                claimed_ids.add(source_id)
                sources.append(source)

        reinforced = item.get("reinforced", False)
        instructions.append(
            FeedbackInstruction(
                id=sources[0].id if sources else None,
                text=text,
                category=item.get("category"),
                scope=item.get("scope"),
                persistent=item.get("persistent", True),
                # 統合元の言及回数を合算し、今回改めて言及されたものだけ1回加算する
                weight=sum(s.weight for s in sources) + (1 if reinforced else 0),
                created_at=min((s.created_at for s in sources), default=now),
                last_reinforced_at=now if reinforced else max((s.last_reinforced_at for s in sources), default=now),
            )
        )

    instructions = apply_limits(instructions)
    repo.save_instructions(instructions, [p.id for p in profile.pending])
    logger.info(f"Feedback consolidated: {len(profile.pending)} pending -> {len(instructions)} instructions")

    profile.instructions = instructions
    profile.pending = []
    return profile


def _build_feedback_instructions_text(summary_type):
    """該当サマリー種別に効くフィードバック指示を、分析プロンプトへ注入する形に整えて返す"""
    try:
        profile = _consolidate_feedback()
        return build_instructions_text(profile.instructions_for(summary_type))
    except Exception as e:
        # フィードバックが取れなくても分析自体は続行させる
        logger.warning(f"Failed to build feedback instructions: {e}")
        return None


def _drop_used_transient_instructions(summary_type):
    """今回の生成で使い切った1回きりの指示を破棄する"""
    try:
        repo = FeedbackProfileRepository()
        repo.remove_instructions(repo.load().transient_instruction_ids(summary_type))
    except Exception as e:
        logger.warning(f"Failed to drop transient feedback instructions: {e}")


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
        """
        フィードバックを保存し、正規化を今すぐ実行すべきかを返す。

        生テキストはサマリー文書に残しつつ(どのサマリーへの感想かを追える形で残すため)、
        以降の分析へ恒久的に反映するためプロファイルの未正規化キューにも積む。
        正規化はAI呼び出しを伴うので、実行の判断と実施は呼び出し側に委ねる。
        """
        SummaryRepository().update_feedback(summary_id, feedback)

        profile_repo = FeedbackProfileRepository()
        profile_repo.add_pending(feedback, summary_id)
        return len(profile_repo.load().pending) >= PENDING_CONSOLIDATION_THRESHOLD

    def consolidate_feedback(self):
        """未正規化フィードバックを指示リストへ統合する(バックグラウンド実行を想定)"""
        _consolidate_feedback()

    def get_feedback_profile_view(self):
        """
        設定画面向けに、AIが記憶している指示と未反映フィードバックの件数を返す。

        指示と件数で2度DBを読まないよう、1回のロードから両方を組み立てる。
        """
        profile = FeedbackProfileRepository().load()
        return {
            "instructions": profile.sorted_instructions(),
            "pending_count": len(profile.pending),
        }

    def delete_feedback_instruction(self, instruction_id):
        """ユーザーが不要と判断した指示を削除し、以降の分析へ渡らないようにする"""
        FeedbackProfileRepository().remove_instructions([instruction_id])

    def start_weekly_summary(self):
        now = datetime.now()
        period_end = now
        period_start = now - timedelta(days=7)
        period_label = f"{period_start.strftime('%Y/%m/%d')}〜{period_end.strftime('%Y/%m/%d')}の1週間"
        return self._start_summary("weekly", period_start, period_end, period_label)

    def start_monthly_summary(self):
        now = datetime.now()
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = first_of_this_month - timedelta(microseconds=1)
        period_start = period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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
            summary_repo.update_summary(
                summary_id,
                {
                    "status": "failed",
                    "content_analysis": "この期間には投稿がありませんでした。",
                },
            )
            return

        # Convert posts to plain text
        posts_text = ""
        for i, post in enumerate(posts, 1):
            plain = html_to_plain_text(post.content)
            timestamp = post.timestamp.strftime("%Y/%m/%d %H:%M")
            posts_text += f"{i}. [{timestamp}] {plain}\n"

        # 過去のフィードバックを正規化した指示を、毎回まとめてプロンプトへ注入する
        feedback_instructions_text = _build_feedback_instructions_text(summary_type)

        # Build scores history from past summaries
        past_summaries = summary_repo.find_by_type(summary_type)
        scores_history = []
        for s in reversed(past_summaries):
            if s.status == "completed":
                scores_history.append(
                    {
                        "date": s.period_end.strftime("%m/%d"),
                        "stress": s.stress_score,
                        "happiness": s.happiness_score,
                        "sentiment": s.sentiment_score,
                    }
                )
        # Keep last 12 data points for the trend chart
        scores_history = scores_history[-12:]

        search_history_text = _build_search_history_text(period_start, period_end)

        try:
            ai_service = AIClient()
            result = ai_service.analyze_posts(
                posts_text, summary_type, period_label, feedback_instructions_text, search_history_text
            )

            # Append current scores to history
            scores_history.append(
                {
                    "date": period_end.strftime("%m/%d"),
                    "stress": result["stress_score"],
                    "happiness": result["happiness_score"],
                    "sentiment": result["sentiment_score"],
                }
            )

            summary_repo.update_summary(
                summary_id,
                {
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
                },
            )
            logger.info(f"{summary_type} summary generated: {summary_id}")
            _drop_used_transient_instructions(summary_type)

        except Exception as e:
            logger.error(f"Failed to generate {summary_type} summary: {e}")
            summary_repo.update_summary(
                summary_id,
                {
                    "post_count": len(posts),
                    "status": "failed",
                    "content_analysis": f"サマリー生成中にエラーが発生しました: {str(e)}",
                },
            )

    def get_dashboard_data(self, summary_type):
        """ダッシュボード用にサマリーのスコア推移データを集約して返す"""
        summary_repo = SummaryRepository()
        summaries = summary_repo.find_by_type(summary_type)

        # completedのみ、古い順にソート
        completed = [s for s in summaries if s.status == "completed"]
        completed.reverse()

        labels = []
        stress = []
        happiness = []
        sentiment = []
        for s in completed:
            labels.append(s.period_end.strftime("%m/%d"))
            stress.append(s.stress_score)
            happiness.append(s.happiness_score)
            sentiment.append(s.sentiment_score)

        latest = None
        if completed:
            s = completed[-1]
            latest = {
                "stress_score": s.stress_score,
                "happiness_score": s.happiness_score,
                "sentiment_score": s.sentiment_score,
                "emoji_expression": s.emoji_expression,
                "period_label": f"{s.period_start.strftime('%Y/%m/%d')} — {s.period_end.strftime('%Y/%m/%d')}",
                "post_count": s.post_count,
            }

        return {
            "labels": labels,
            "stress": stress,
            "happiness": happiness,
            "sentiment": sentiment,
            "latest": latest,
        }

    # Keep synchronous methods for scheduler compatibility
    def generate_weekly_summary(self):
        now = datetime.now()
        period_end = now
        period_start = now - timedelta(days=7)
        period_label = f"{period_start.strftime('%Y/%m/%d')}〜{period_end.strftime('%Y/%m/%d')}の1週間"
        return self._generate_summary("weekly", period_start, period_end, period_label)

    def generate_monthly_summary(self):
        now = datetime.now()
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = first_of_this_month - timedelta(microseconds=1)
        period_start = period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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

        # 過去のフィードバックを正規化した指示を、毎回まとめてプロンプトへ注入する
        feedback_instructions_text = _build_feedback_instructions_text(summary_type)

        # Build scores history from past summaries
        past_summaries = summary_repo.find_by_type(summary_type)
        scores_history = []
        for s in reversed(past_summaries):
            if s.status == "completed":
                scores_history.append(
                    {
                        "date": s.period_end.strftime("%m/%d"),
                        "stress": s.stress_score,
                        "happiness": s.happiness_score,
                        "sentiment": s.sentiment_score,
                    }
                )
        # Keep last 12 data points for the trend chart
        scores_history = scores_history[-12:]

        search_history_text = _build_search_history_text(period_start, period_end)

        try:
            ai_service = AIClient()
            result = ai_service.analyze_posts(
                posts_text, summary_type, period_label, feedback_instructions_text, search_history_text
            )

            # Append current scores to history
            scores_history.append(
                {
                    "date": period_end.strftime("%m/%d"),
                    "stress": result["stress_score"],
                    "happiness": result["happiness_score"],
                    "sentiment": result["sentiment_score"],
                }
            )

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
            _drop_used_transient_instructions(summary_type)
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
