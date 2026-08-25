"""
[domain] サマリーエンティティ

概要:
  AIによる投稿分析結果を表すドメインモデル。
  週次・月次で生成され、ストレススコア・幸福度・感情スコア・
  トピック抽出・カウンセリングメッセージなどを保持する。
  ユーザーが残したフィードバックの原文も保持する(以降の分析への反映は
  FeedbackProfileが担う)。
"""


class Summary:
    def __init__(
        self,
        type,
        period_start,
        period_end,
        post_count=0,
        stress_score=0,
        happiness_score=0,
        sentiment_score=0.0,
        emoji_expression="",
        top_topics=None,
        content_analysis="",
        advice="",
        encouragement="",
        scores_history=None,
        feedback=None,
        feedback_at=None,
        status="completed",
        id=None,
        created_at=None,
    ):
        self.id = id
        self.type = type  # "weekly" or "monthly"
        self.period_start = period_start
        self.period_end = period_end
        self.post_count = post_count
        self.stress_score = stress_score  # 0-100
        self.happiness_score = happiness_score  # 0-100
        self.sentiment_score = sentiment_score  # -1.0 ~ 1.0
        self.emoji_expression = emoji_expression
        self.top_topics = top_topics or []
        self.content_analysis = content_analysis
        self.advice = advice
        self.encouragement = encouragement
        self.scores_history = scores_history or []  # [{date, stress, happiness, sentiment}]
        self.feedback = feedback
        self.feedback_at = feedback_at
        self.status = status  # "completed" or "failed"
        self.created_at = created_at
