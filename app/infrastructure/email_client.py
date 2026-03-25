"""
[infrastructure] メール送信クライアント

概要:
  SendGrid APIを使ったメール送信を担当する外部APIクライアント。
  サマリー生成完了時に、登録済みメールアドレス宛に結果を送信する。
"""

import logging
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import HtmlContent, Mail

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable is not set")
        self.client = SendGridAPIClient(self.api_key)

    def send_summary_email(self, to_email, summary):
        """サマリー結果をメールで送信する"""
        subject = self._build_subject(summary)
        html_content = self._build_html(summary)

        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=HtmlContent(html_content),
        )

        try:
            response = self.client.send(message)
            logger.info(f"Email sent to {to_email}: status={response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _build_subject(self, summary):
        type_label = "週次" if summary.type == "weekly" else "月次"
        period_end = summary.period_end.strftime("%Y/%m/%d")
        return f"【GRUMBLER】{type_label}サマリー ({period_end}) {summary.emoji_expression}"

    def _build_html(self, summary):
        type_label = "週次" if summary.type == "weekly" else "月次"
        period_start = summary.period_start.strftime("%Y/%m/%d")
        period_end = summary.period_end.strftime("%Y/%m/%d")
        topics_html = "".join(f"<li>{topic}</li>" for topic in (summary.top_topics or []))

        return f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                {summary.emoji_expression} {type_label}サマリー
            </h2>
            <p style="color: #666; font-size: 14px;">
                期間: {period_start} 〜 {period_end} ／ 投稿数: {summary.post_count}件
            </p>

            <div style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="color: #444; margin-top: 0;">📊 スコア</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px;">ストレスレベル</td>
                        <td style="padding: 8px; font-weight: bold;">{summary.stress_score}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">幸福度</td>
                        <td style="padding: 8px; font-weight: bold;">{summary.happiness_score}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">感情スコア</td>
                        <td style="padding: 8px; font-weight: bold;">{summary.sentiment_score}</td>
                    </tr>
                </table>
            </div>

            <div style="margin: 16px 0;">
                <h3 style="color: #444;">🏷️ 主なトピック</h3>
                <ul style="color: #555;">{topics_html}</ul>
            </div>

            <div style="margin: 16px 0;">
                <h3 style="color: #444;">📝 分析</h3>
                <p style="color: #555; line-height: 1.6;">{summary.content_analysis}</p>
            </div>

            <div style="background: #e8f5e9; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="color: #2e7d32; margin-top: 0;">💡 アドバイス</h3>
                <p style="color: #555; line-height: 1.6;">{summary.advice}</p>
            </div>

            <div style="background: #fff3e0; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="color: #e65100; margin-top: 0;">🌟 励まし</h3>
                <p style="color: #555; line-height: 1.6;">{summary.encouragement}</p>
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
            <p style="color: #999; font-size: 12px; text-align: center;">
                このメールはGRUMBLERから自動送信されています。
            </p>
        </div>
        """
