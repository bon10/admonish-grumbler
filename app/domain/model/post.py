"""
[domain] 投稿エンティティ

概要:
  ユーザーが投稿する愚痴・つぶやきを表すドメインモデル。
  投稿内容(content)、投稿日時(timestamp)、識別子(id)を保持する。
"""


class Post:
    def __init__(self, content, timestamp, id=None):
        self.content = content
        self.timestamp = timestamp
        self.id = id
