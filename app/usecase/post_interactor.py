"""
[usecase] 投稿ユースケース

概要:
  投稿(Post)に関するアプリケーションロジックを制御する。
  投稿の作成(Markdown変換・リンク化・OGPプレビュー付与)、
  一覧取得(ページネーション・JST変換)、更新、削除を担当する。
  infrastructure層のRepository・Converter・OpenGraphClientを組み合わせて処理を実行する。
"""
import logging
import re

import pytz

from app.infrastructure.message_converter import MessageConverter
from app.infrastructure.opengraph_client import OpenGraphClient
from app.infrastructure.post_repository import PostRepository

# UTCのタイムゾーンオブジェクト
utc_timezone = pytz.timezone("UTC")

# JSTのタイムゾーンオブジェクト
jst_timezone = pytz.timezone("Asia/Tokyo")


class PostInteractor:
    def create_post(self, content):
        post_repository = PostRepository()
        # まずはマークダウンに変換
        converted_markdown = MessageConverter.convert_markdown(content)
        # HTMLをリンクに変換
        converted_html = MessageConverter.convert_message(converted_markdown)
        # ログ出力
        logging.info(f"Converted HTML: {converted_html}")
        # <a href="...">タグからURLを抽出
        urls = re.findall(r'href="([^"]+)"', converted_html)
        for url in urls:
            opengraph_preview = OpenGraphClient.generate_opengraph_preview(url)
            if opengraph_preview:
                converted_html += opengraph_preview
        post = post_repository.save(converted_html)
        logging.info(f"New post created: {post}")
        return post

    def get_all_posts(self):
        post_repository = PostRepository()
        return post_repository.find_all()

    def get_posts_by_page(self, page_number, posts_per_page):
        post_repository = PostRepository()

        posts = post_repository.find_by_page(page_number, posts_per_page)
        for post in posts:
            # Markdownに変換
            # converted_markdown = MessageConverter.convert_markdown(post.content)
            # さらにテキストを読みやすく変更（改行・HTMLのリンク化）
            # converted_message = MessageConverter.convert_message(post.content)

            # post.content = converted_message

            # 時間をJSTに変更
            utc_time = post.timestamp
            jst_time = utc_time.replace(tzinfo=utc_timezone).astimezone(jst_timezone)
            post.timestamp = jst_time
        return posts

    def get_total_post_count(self):
        post_repository = PostRepository()
        return post_repository.get_total_post_count()

    def update_post(self, post_id, content):
        post_repository = PostRepository()
        converted_markdown = MessageConverter.convert_markdown(content)
        converted_html = MessageConverter.convert_message(converted_markdown)
        urls = re.findall(r'href="([^"]+)"', converted_html)
        for url in urls:
            opengraph_preview = OpenGraphClient.generate_opengraph_preview(url)
            if opengraph_preview:
                converted_html += opengraph_preview
        return post_repository.update_by_id(post_id, converted_html)

    def delete_post(self, post_id):
        post_repository = PostRepository()
        return post_repository.delete_by_id(post_id)
