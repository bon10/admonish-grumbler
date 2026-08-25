"""
[interface] サマリーコントローラ

概要:
  AI要約(Summary)に関するHTTPエンドポイントを定義するFlask Blueprint。
  GET /summaries(一覧)、GET /summary/<id>(詳細)、POST /summary/<id>/feedback(フィードバック)、
  POST /summary/generate(生成)、GET /summary/<id>/status(生成状況確認)、
  POST /feedback-instructions/<id>/delete(記憶した指示の削除)を提供する。
  サマリー生成はAI呼び出しの完了を待って結果を返す。
  フィードバックの指示への正規化もAI呼び出しを伴うため、投稿者を待たせないよう
  バックグラウンドスレッドで実行する。
"""
import threading

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from app.usecase.summary_interactor import SummaryInteractor

bp = Blueprint("summary", __name__)
summary_interactor = SummaryInteractor()


@bp.route("/summaries")
def list_summaries():
    summaries = summary_interactor.get_all_summaries()
    return render_template("summary_list.html", summaries=summaries)


@bp.route("/summary/<summary_id>")
def detail(summary_id):
    summary = summary_interactor.get_summary_by_id(summary_id)
    if not summary:
        flash("サマリーが見つかりませんでした")
        return redirect(url_for("summary.list_summaries"))
    return render_template("summary_detail.html", summary=summary)


@bp.route("/summary/<summary_id>/feedback", methods=["POST"])
def feedback(summary_id):
    feedback_text = request.form.get("feedback", "").strip()
    if feedback_text:
        needs_consolidation = summary_interactor.save_feedback(summary_id, feedback_text)
        flash("フィードバックを保存しました")
        if needs_consolidation:
            # 正規化はAI呼び出しを伴うため、ユーザーを待たせないようバックグラウンドで実行する。
            # デプロイ先(Vercel)ではレスポンス送信後にこのスレッドが打ち切られることがあるが、
            # 未正規化のフィードバックは次回のサマリー生成時にまとめて正規化されるため、
            # 打ち切られても取りこぼしにはならない。
            app = current_app._get_current_object()

            def consolidate_in_background():
                with app.app_context():
                    summary_interactor.consolidate_feedback()

            threading.Thread(target=consolidate_in_background).start()
    return redirect(url_for("summary.detail", summary_id=summary_id))


@bp.route("/feedback-instructions/<instruction_id>/delete", methods=["POST"])
def delete_feedback_instruction(instruction_id):
    summary_interactor.delete_feedback_instruction(instruction_id)
    flash("指示を削除しました")
    return redirect(url_for("user.settings"))


@bp.route("/summary/generate", methods=["POST"])
def generate():
    """
    サマリーを生成し、完了してからレスポンスを返す。

    デプロイ先(Vercel)はレスポンス送信後に関数の実行を止めるため、
    生成をバックグラウンドスレッドに逃がすと処理が完了せず
    サマリーがgeneratingのまま取り残される。そのため同期的に実行する。
    クライアントは戻り値のsummary_idでステータスを確認するので、
    完了後に返しても画面側の流れは変わらない。
    """
    summary_type = request.form.get("type", "weekly")
    summary_id, s_type, period_start, period_end, period_label = summary_interactor.start_summary(summary_type)
    summary_interactor.run_generation(summary_id, s_type, period_start, period_end, period_label)

    return jsonify({"summary_id": summary_id, "status": summary_interactor.get_summary_status(summary_id)})


@bp.route("/summary/<summary_id>/status")
def status(summary_id):
    s = summary_interactor.get_summary_status(summary_id)
    if s is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"summary_id": summary_id, "status": s})
