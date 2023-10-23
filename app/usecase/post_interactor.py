import datetime
import logging
from datetime import datetime

import pytz

from app.domain.services.message_converter import MessageConverter
from app.infrastructure.post_repository import PostRepository

# UTCのタイムゾーンオブジェクト
utc_timezone = pytz.timezone('UTC')

# JSTのタイムゾーンオブジェクト
jst_timezone = pytz.timezone('Asia/Tokyo')


class PostInteractor:
    def create_post(self, content):
        post_repository = PostRepository()
        post = post_repository.save(content)
        logging.info(f'New post created: {post}')
        return post

    def get_all_posts(self):
        post_repository = PostRepository()
        return post_repository.find_all()

    def get_posts_by_page(self, page_number, posts_per_page):
        post_repository = PostRepository()

        posts = post_repository.find_by_page(page_number, posts_per_page)
        for post in posts:
            # Markdownに変換
            converted_message = MessageConverter.convert_markdown(
                post.content)
            # さらにテキストを読みやすく変更（改行・HTMLのリンク化）
            converted_message = MessageConverter.convert_message(
                converted_message)

            post.content = converted_message

            # 時間をJSTに変更
            utc_time = post.timestamp
            jst_time = utc_time.replace(
                tzinfo=utc_timezone).astimezone(jst_timezone)
            post.timestamp = jst_time
        return posts

    def get_total_post_count(self):
        post_repository = PostRepository()
        return post_repository.get_total_post_count()
