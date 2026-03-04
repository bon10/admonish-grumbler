import json
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "stress_score": {"type": "integer", "description": "ストレスレベル 0-100"},
        "happiness_score": {"type": "integer", "description": "幸福度 0-100"},
        "sentiment_score": {"type": "number", "description": "感情スコア -1.0(非常にネガティブ)〜1.0(非常にポジティブ)"},
        "emoji_expression": {"type": "string", "description": "この期間の気分を表す絵文字1つ"},
        "top_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "主要なトピック(最大5つ)",
        },
        "content_analysis": {"type": "string", "description": "投稿内容の総合分析(200-400字)"},
        "advice": {"type": "string", "description": "メンタルヘルスの観点からのアドバイス(200-300字)"},
        "encouragement": {"type": "string", "description": "ユーザーへの励ましのメッセージ(100-200字)"},
    },
    "required": [
        "stress_score",
        "happiness_score",
        "sentiment_score",
        "emoji_expression",
        "top_topics",
        "content_analysis",
        "advice",
        "encouragement",
    ],
}


def build_prompt(posts_text, period_type, period_label, previous_feedback=None):
    feedback_section = ""
    if previous_feedback:
        feedback_section = f"""

【前回のユーザーフィードバック】
ユーザーは前回のサマリーに対して以下の感想を残しています。この内容を今回の分析に反映してください:
「{previous_feedback}」
"""

    return f"""あなたはメンタルヘルスカウンセラーです。
以下は、あるユーザーが{period_label}に投稿した愚痴・つぶやきの一覧です。
これらの投稿を分析し、ユーザーのメンタル状態を評価してください。

【分析の指針】
- ストレスレベル(stress_score): 投稿内容からストレスの度合いを0-100で評価
- 幸福度(happiness_score): ポジティブな要素や楽しい話題の割合から0-100で評価
- 感情スコア(sentiment_score): 全体的な感情の傾向を-1.0〜1.0で評価
- 絵文字(emoji_expression): この期間の気分を最もよく表す絵文字を1つ選択
- トピック(top_topics): 主に話題にしているテーマを最大5つ抽出
- 内容分析(content_analysis): カウンセラーの視点で投稿傾向を分析
- アドバイス(advice): 具体的で実践可能なメンタルケアのアドバイス
- 励まし(encouragement): 温かく寄り添うメッセージ
{feedback_section}
【投稿一覧】({period_type}サマリー)
{posts_text}
"""


class AIService:
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
