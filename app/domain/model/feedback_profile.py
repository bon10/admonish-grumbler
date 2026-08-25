"""
[domain] フィードバックプロファイルエンティティ

概要:
  ユーザーがサマリーに残したフィードバックを、AI分析へ恒久的に反映するための
  ドメインモデル。正規化済みの指示(FeedbackInstruction)の集合と、
  まだ正規化されていない生フィードバック(pending)を保持する。
  指示リストを件数・文字数の上限内に保つ減衰ロジックと、
  サマリー種別(weekly/monthly)による適用範囲の絞り込みを担う。
"""

import uuid
from datetime import datetime

# 指示リストの上限。AIへのプロンプトが投稿本文を圧迫しない分量に抑えるための値。
MAX_INSTRUCTIONS = 12
MAX_TOTAL_CHARS = 1500

# 指示の分類。AI側にもこの値を列挙して返させる。
CATEGORY_STYLE = "style"
CATEGORY_FOCUS = "focus"
CATEGORY_CORRECTION = "correction"
CATEGORY_TONE = "tone"
CATEGORIES = (CATEGORY_STYLE, CATEGORY_FOCUS, CATEGORY_CORRECTION, CATEGORY_TONE)

CATEGORY_LABELS = {
    CATEGORY_STYLE: "文体",
    CATEGORY_FOCUS: "着眼点",
    CATEGORY_CORRECTION: "訂正",
    CATEGORY_TONE: "トーン",
}

# 指示の適用範囲。"all"は週次・月次の両方に適用される。
SCOPE_ALL = "all"
SCOPE_WEEKLY = "weekly"
SCOPE_MONTHLY = "monthly"
SCOPES = (SCOPE_ALL, SCOPE_WEEKLY, SCOPE_MONTHLY)

SCOPE_LABELS = {
    SCOPE_ALL: "全体",
    SCOPE_WEEKLY: "週次",
    SCOPE_MONTHLY: "月次",
}


class FeedbackInstruction:
    """正規化された1件の指示。ユーザーの生フィードバックをAIが要求単位に分解したもの。"""

    def __init__(
        self,
        text,
        category=CATEGORY_STYLE,
        scope=SCOPE_ALL,
        persistent=True,
        weight=1,
        id=None,
        created_at=None,
        last_reinforced_at=None,
    ):
        now = datetime.now()
        self.id = id or str(uuid.uuid4())
        self.text = text
        self.category = category if category in CATEGORIES else CATEGORY_STYLE
        self.scope = scope if scope in SCOPES else SCOPE_ALL
        self.persistent = persistent
        # ユーザーが同じ趣旨のフィードバックを繰り返した回数。減衰時の優先度に使う。
        self.weight = max(1, weight)
        self.created_at = created_at or now
        self.last_reinforced_at = last_reinforced_at or now

    @property
    def category_label(self):
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def scope_label(self):
        return SCOPE_LABELS.get(self.scope, self.scope)

    def applies_to(self, summary_type):
        return self.scope == SCOPE_ALL or self.scope == summary_type


class FeedbackPendingItem:
    """まだ指示へ正規化されていない生のフィードバック。"""

    def __init__(self, text, summary_id=None, id=None, created_at=None):
        self.id = id or str(uuid.uuid4())
        self.text = text
        self.summary_id = summary_id
        self.created_at = created_at or datetime.now()


class FeedbackProfile:
    """指示リストと未正規化フィードバックを束ねる、アプリ全体で1つだけ存在するプロファイル。"""

    def __init__(self, instructions=None, pending=None, updated_at=None):
        self.instructions = instructions or []
        self.pending = pending or []
        self.updated_at = updated_at

    def sorted_instructions(self):
        """すべての指示を優先度(言及回数→最終言及日)の高い順に返す"""
        return sorted(self.instructions, key=_priority_key, reverse=True)

    def instructions_for(self, summary_type):
        """指定サマリー種別に適用される指示のみを、優先度の高い順に返す"""
        return [i for i in self.sorted_instructions() if i.applies_to(summary_type)]

    def transient_instruction_ids(self, summary_type):
        """
        指定サマリー種別に適用された1回きりの指示(persistent=False)のIDを返す。

        生成後に破棄するために使う。週次の生成が、月次だけに向けられた
        1回きりの指示を使われないまま捨てないよう、適用範囲で絞り込む。
        """
        return [i.id for i in self.instructions if not i.persistent and i.applies_to(summary_type)]


def apply_limits(instructions):
    """
    指示リストを上限(件数・総文字数)内に収める。

    優先度は weight(言及回数)の多さ、次いで last_reinforced_at(最終言及日)の新しさ。
    ユーザーが繰り返し求めている指示ほど残り、久しく言及されない指示から落ちていく。
    """
    ordered = sorted(instructions, key=_priority_key, reverse=True)

    kept = []
    total_chars = 0
    for instruction in ordered:
        if len(kept) >= MAX_INSTRUCTIONS:
            break
        length = len(instruction.text)
        if total_chars + length > MAX_TOTAL_CHARS:
            continue
        kept.append(instruction)
        total_chars += length
    return kept


def _priority_key(instruction):
    return (instruction.weight, instruction.last_reinforced_at)
