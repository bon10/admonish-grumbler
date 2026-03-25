"""
[interface] ダッシュボードコントローラ

概要:
  スコア推移のダッシュボードページを提供するFlask Blueprint。
  GET /dashboard(ページ表示)、GET /dashboard/data(JSON API)を定義する。
"""

from flask import Blueprint, jsonify, render_template, request

from app.usecase.summary_interactor import SummaryInteractor

bp = Blueprint("dashboard", __name__)
summary_interactor = SummaryInteractor()


@bp.route("/dashboard")
def index():
    return render_template("dashboard.html")


@bp.route("/dashboard/data")
def data():
    summary_type = request.args.get("type", "weekly")
    if summary_type not in ("weekly", "monthly"):
        summary_type = "weekly"
    result = summary_interactor.get_dashboard_data(summary_type)
    return jsonify(result)
