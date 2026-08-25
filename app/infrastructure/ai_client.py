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


class AIClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

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
