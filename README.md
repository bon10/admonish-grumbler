## What is this?

This is my own application for posting Twitter-like tweets.
Tweets are stored in MongoDB.

- Python + Flask
- MongoDB

### Features to be supported in the near future

- Real-time tweet acquisition (use Change Streams for MongoDB)
- infinity scroll
- Markdown support for tweets

## How to Develop

```
% docker compose up -d
% docker exec -it admonish-grumbler-app /bin/bash
# pip install --upgrade pip
# pip install -r requirements.txt
# python run.py
```

Access to http://localhost:5500 from your browser.

If you add a new package, please update requirements.txt.

```
pip freeze > requirements.txt
```

## ディレクトリ構成

このアプリケーションのディレクトリ構成は以下のようになっています：

- `app/`: アプリケーションのルートディレクトリです。
  - `application/`: アプリケーションのビジネスロジックを含むディレクトリです。
  - `domain/`: ドメインロジックが配置されるディレクトリです。
    - `model/`: アプリケーションのエンティティモデルが定義されます。
    - `services/`: ドメインロジックの一部としてビジネスロジックを含むサービスが配置されます。
  - `infrastructure/`: アプリケーションのインフラストラクチャ関連のコードが配置されるディレクトリです。
  - `interface/`: アプリケーションの外部とのインタフェースを扱うディレクトリです。
    - `http/`: HTTP 関連の処理が含まれます（ルーティング、ミドルウェアなど）。
  - `static/`: アプリケーションで使用される静的ファイルが配置されるディレクトリです。
    - `images/`: 画像ファイルが含まれます。
    - `js/`: JavaScript ファイルが含まれます。
  - `templates/`: アプリケーションの HTML テンプレートが配置されるディレクトリです。
  - `usecase/`: アプリケーションのユースケース（use case）が配置されるディレクトリです。
- `config.py`: アプリケーションの設定ファイルです。
- `docker/`: Docker 関連のファイルが配置されるディレクトリです。
- `docker-compose.yml`: Docker Compose ファイルです。
- `requirements.txt`: アプリケーションが依存する Python パッケージのリストが含まれます。
- `run.py`: アプリケーションを実行するためのエントリーポイントです。
