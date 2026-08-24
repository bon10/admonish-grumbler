"""
[interface] サマリーコントローラ

概要:
  AI要約(Summary)に関するHTTPエンドポイントを定義するFlask Blueprint。
  GET /summaries(一覧)、GET /summary/<id>(詳細)、POST /summary/<id>/feedback(フィードバック)、
  POST /summary/generate(非同期生成開始)、GET /summary/<id>/status(生成状況確認)を提供する。
  サマリー生成はバックグラウンドスレッドで実行し、クライアントはポーリングで完了を確認する。
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
        summary_interactor.save_feedback(summary_id, feedback_text)
        flash("フィードバックを保存しました")
    return redirect(url_for("summary.detail", summary_id=summary_id))


@bp.route("/summary/generate", methods=["POST"])
def generate():
    summary_type = request.form.get("type", "weekly")
    if summary_type == "monthly":
        result = summary_interactor.start_monthly_summary()
    else:
        result = summary_interactor.start_weekly_summary()

    summary_id, s_type, period_start, period_end, period_label = result

    app = current_app._get_current_object()

    def run_in_background():
        with app.app_context():
            summary_interactor.run_generation(summary_id, s_type, period_start, period_end, period_label)

    thread = threading.Thread(target=run_in_background)
    thread.start()

    return jsonify({"summary_id": summary_id, "status": "generating"})


@bp.route("/summary/<summary_id>/status")
def status(summary_id):
    s = summary_interactor.get_summary_status(summary_id)
    if s is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"summary_id": summary_id, "status": s})
