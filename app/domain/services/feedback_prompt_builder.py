"""
[domain] フィードバック正規化用プロンプトビルダー

概要:
  ユーザーの生フィードバックを、AI分析に注入できる「指示」へ正規化するための
  プロンプト文とレスポンススキーマを定義する。
  build_merge_prompt()で既存指示と新規フィードバックの統合を指示し、
  build_instructions_text()で分析プロンプトへ注入する箇条書きを組み立てる。
  外部ライブラリに依存しない純粋なドメインサービス。
"""

from app.domain.model.feedback_profile import (
    CATEGORIES,
    MAX_INSTRUCTIONS,
    MAX_TOTAL_CHARS,
    SCOPES,
)

FEEDBACK_MERGE_SCHEMA = {
    "type": "object",
    "properties": {
        "instructions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "AIへの指示を1文で表現したもの(60字以内)",
                    },
                    "category": {
                        "type": "string",
                        "enum": list(CATEGORIES),
                        "description": "style(文体) / focus(着眼点) / correction(誤解の訂正) / tone(トーン)",
                    },
                    "scope": {
                        "type": "string",
                        "enum": list(SCOPES),
                        "description": "all(週次・月次の両方) / weekly(週次のみ) / monthly(月次のみ)",
                    },
                    "persistent": {
                        "type": "boolean",
                        "description": "今後ずっと守るべき指示ならtrue、その回限りの感想ならfalse",
                    },
                    "reinforced": {
                        "type": "boolean",
                        "description": "今回の新規フィードバックがこの指示の内容を含んでいるならtrue",
                    },
                    "source_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "この指示に統合された既存指示のID。新規の指示なら空配列",
                    },
                },
                "required": ["text", "category", "scope", "persistent", "reinforced", "source_ids"],
            },
        }
    },
    "required": ["instructions"],
}


def build_merge_prompt(existing_instructions, pending_texts):
    """既存の指示リストと新規フィードバックを、重複なく統合するようAIに指示する"""
    if existing_instructions:
        existing_lines = "\n".join(
            f"- ID:{i.id} [{i.category}/{i.scope}] {i.text}" for i in existing_instructions
        )
    else:
        existing_lines = "(まだ登録されている指示はありません)"

    pending_lines = "\n".join(f"{n}. 「{text}」" for n, text in enumerate(pending_texts, 1))

    return f"""あなたは、メンタルヘルス分析AIの振る舞いを調整する設定管理者です。
ユーザーが分析結果に対して残した感想を、分析AIが従うべき「指示」の一覧へ正規化してください。

【現在登録されている指示】
{existing_lines}

【今回新しく届いたユーザーの感想】
{pending_lines}

【正規化のルール】
- 新しい感想から読み取れる要求を、それぞれ1文の指示に分解する
- 既存の指示と同じ趣旨のものは1つにまとめ、まとめた既存指示のIDを source_ids に列挙する
- 既存の指示と矛盾する要求が来た場合は、新しい要求で置き換える。置き換えられる既存指示のIDを source_ids に入れる
- 内容が変わらない既存の指示も、そのまま出力に含める(text をそのまま書き、source_ids に自身のIDを入れる)
- 今回の感想に含まれていた指示は reinforced を true にする。既存のまま変化がないものは false
- 「今回の分析は的外れだった」のようなその回限りの感想は persistent を false にする。
  「今後は〜してほしい」のような継続的な要求は true にする
- 感想が週次サマリーだけ、月次サマリーだけに向けられている場合は scope をそれぞれ weekly / monthly にする。
  判断がつかない場合は all にする
- 指示は分析AIが実行できる具体的な表現にする。「良い感じにして」のような曖昧な指示にはしない
- 出力する指示は最大{MAX_INSTRUCTIONS}件、全体で{MAX_TOTAL_CHARS}字以内に収める。
  収まらない場合は、繰り返し言及されている要求を優先して残す
"""


def build_instructions_text(instructions):
    """分析プロンプトへ注入する指示の箇条書きを組み立てる。指示が無ければNoneを返す。"""
    if not instructions:
        return None
    return "\n".join(f"- [{i.category_label}] {i.text}" for i in instructions)
