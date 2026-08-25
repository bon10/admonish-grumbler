"""
[domain] AI分析用プロンプトビルダー

概要:
  投稿分析に使用するプロンプト文とレスポンススキーマを定義する。
  build_prompt()でカウンセラー視点の分析指示を組み立て、
  ANALYSIS_SCHEMAでAIの出力形式(スコア・トピック・アドバイス等)を規定する。
  外部ライブラリに依存しない純粋なドメインサービス。
"""

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "stress_score": {"type": "integer", "description": "ストレスレベル 0-100"},
        "happiness_score": {"type": "integer", "description": "幸福度 0-100"},
        "sentiment_score": {
            "type": "number",
            "description": "感情スコア -1.0(非常にネガティブ)〜1.0(非常にポジティブ)",
        },
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


def build_prompt(posts_text, period_type, period_label, feedback_instructions_text=None, search_history_text=None):
    feedback_section = ""
    if feedback_instructions_text:
        feedback_section = f"""

【ユーザーからの継続的な要望】
ユーザーが過去のサマリーに対して残した感想を、守るべき指示として整理したものです。
今回の分析でも必ず守ってください:
{feedback_instructions_text}
"""

    search_section = ""
    if search_history_text:
        search_section = f"""

【この期間の検索履歴】
ユーザーがこの期間中に検索したキーワードの一覧です。
何を気にしていたか、どんなトピックに関心を持っていたかの参考にしてください:
{search_history_text}
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
- 内容分析(content_analysis): カウンセラーの視点で投稿傾向を分析。検索履歴がある場合は、ユーザーが気にしていたテーマについても言及すること
- アドバイス(advice): 具体的で実践可能なメンタルケアのアドバイス
- 励まし(encouragement): 温かく寄り添うメッセージ
{feedback_section}{search_section}
【投稿一覧】({period_type}サマリー)
{posts_text}
"""
