"""
[infrastructure] AI分析クライアント

概要:
  Google Gemini APIを使った投稿分析と、ユーザーフィードバックの指示への正規化を
  担当する外部APIクライアント。
  domain層のai_prompt_builder / feedback_prompt_builderで構築した
  プロンプトとスキーマを使い、Gemini APIにリクエストを送信して
  構造化されたJSON結果を返す。
"""

import json
import logging
import os

from google import genai
from google.genai import types

from app.domain.services.ai_prompt_builder import ANALYSIS_SCHEMA, build_prompt
from app.domain.services.feedback_prompt_builder import FEEDBACK_MERGE_SCHEMA, build_merge_prompt

logger = logging.getLogger(__name__)

# Gemini API側の一時的な過負荷(503 UNAVAILABLE)でサマリー生成を落とさないため、
# 指数バックオフでの再送をSDKに任せる。SDKは再送を設定しないと1回で諦めるため明示する。
# 再送対象のステータス(408/429/5xx)はSDKの既定に従う。
# 生成はVercelの関数内で同期実行するので、待ち時間の合計(約1+2+4+8=15秒)が
# 関数の実行時間上限を食い潰さない範囲に収める。
_RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=5,  # 初回の呼び出しを含む回数
    initial_delay=1.0,
    max_delay=8.0,
)


class AIClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(retry_options=_RETRY_OPTIONS),
        )
        # 挙動を固定したいので安定版を明示する。
        # 旧モデル(gemini-2.5-flash)は新規利用が打ち切られ、APIから移行先として案内された版。
        self.model = "gemini-3.6-flash"

    def analyze_posts(
        self, posts_text, period_type, period_label, feedback_instructions_text=None, search_history_text=None
    ):
        prompt = build_prompt(posts_text, period_type, period_label, feedback_instructions_text, search_history_text)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ANALYSIS_SCHEMA,
                    temperature=0.7,
                ),
            )
            result = json.loads(response.text)
            # Clamp scores to valid ranges
            result["stress_score"] = max(0, min(100, result.get("stress_score", 50)))
            result["happiness_score"] = max(0, min(100, result.get("happiness_score", 50)))
            result["sentiment_score"] = max(-1.0, min(1.0, result.get("sentiment_score", 0.0)))
            return result
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def merge_feedback(self, existing_instructions, pending_texts):
        """
        既存の指示リストと新規フィードバックを統合し、正規化された指示の配列を返す。

        分析と違い創作性は不要で、既存指示の取りこぼしや言い換えを避けたいため、
        temperatureを低く設定する。
        """
        prompt = build_merge_prompt(existing_instructions, pending_texts)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FEEDBACK_MERGE_SCHEMA,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text).get("instructions", [])
        except Exception as e:
            logger.error(f"Gemini API error (feedback merge): {e}")
            raise
