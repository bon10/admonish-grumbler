"""
[infrastructure] AI分析クライアント

概要:
  Google Gemini APIを使った投稿分析を担当する外部APIクライアント。
  domain層のai_prompt_builderで構築したプロンプトとスキーマを使い、
  Gemini APIにリクエストを送信し、構造化されたJSON分析結果を返す。
"""
import json
import logging
import os

from google import genai
from google.genai import types

from app.domain.services.ai_prompt_builder import ANALYSIS_SCHEMA, build_prompt

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def analyze_posts(self, posts_text, period_type, period_label, previous_feedback=None):
        prompt = build_prompt(posts_text, period_type, period_label, previous_feedback)

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
