"""
既存の summaries.feedback を feedback_profile.pending へ取り込むマイグレーション。

背景:
  従来フィードバックは各サマリー文書にのみ保存され、最新1件しか分析へ反映されなかった。
  指示リストによる恒久化(Issue #1)への移行にあたり、それまでに記入済みのフィードバックを
  未正規化キューへ移し、次回のサマリー生成時に指示として取り込まれるようにする。

  サマリー文書側の feedback は監査用にそのまま残す。
  取り込み済みのフィードバックは summary_id で判定するため、再実行しても重複しない。

実行:
  docker exec -it admonish-grumbler-app python scripts/migrate_feedback_to_profile.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.infrastructure.feedback_profile_repository import FeedbackProfileRepository  # noqa: E402


def migrate():
    app = create_app()
    with app.app_context():
        summaries = app.mongo.summaries.find(
            {"feedback": {"$nin": [None, ""]}},
            {"feedback": 1, "feedback_at": 1},
        ).sort("feedback_at", 1)

        repo = FeedbackProfileRepository()
        already_taken = {p.summary_id for p in repo.load().pending}

        migrated = 0
        skipped = 0
        for summary in summaries:
            summary_id = str(summary["_id"])
            if summary_id in already_taken:
                skipped += 1
                continue
            repo.add_pending(summary["feedback"], summary_id)
            migrated += 1

        print(f"取り込み: {migrated}件 / 取り込み済みのためスキップ: {skipped}件")
        print(f"未正規化キュー: {len(repo.load().pending)}件")


if __name__ == "__main__":
    migrate()
