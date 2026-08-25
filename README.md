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

## 環境変数

`.env.sample` をコピーして `.env` を作る。

| 変数                                       | 用途                                                               |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `APP_SECRET_KEY`                           | セッションの署名鍵。変更すると既存のログインセッションは無効になる |
| `MONGO_URI`                                | MongoDB Atlas の接続文字列                                         |
| `GEMINI_API_KEY`                           | サマリー生成に使う AI の API キー                                  |
| `SENDGRID_API_KEY` / `SENDGRID_FROM_EMAIL` | サマリーのメール送信                                               |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH`   | ログインできる唯一の利用者                                         |
| `CRON_SECRET`                              | 定期サマリー生成エンドポイントの呼び出し元認証                     |

`ADMIN_PASSWORD_HASH` は次のコマンドで生成する。依存パッケージはコンテナ側にあるため、コンテナ内で実行する。

```
% docker exec -it admonish-grumbler-app python scripts/generate_password_hash.py
```

## ログイン

利用者は本人 1 人だけなので、ユーザー登録画面は持たない。
`ADMIN_USERNAME` と `ADMIN_PASSWORD_HASH` が資格情報の唯一の出所で、DB には保存しない。

`/login` と静的ファイル以外のすべての画面はログイン必須。
どちらかの環境変数が未設定の場合、誰もログインできない状態になる。

## 定期サマリー生成

週次・月次サマリーの自動生成は、**起動のきっかけだけが環境によって違い、生成処理は共通**（`SummaryInteractor.generate_scheduled_summary`）。

|                | 起動するもの                               | 設定                               |
| -------------- | ------------------------------------------ | ---------------------------------- |
| ローカル       | アプリ内スケジューラ（`app/scheduler.py`） | `ENABLE_IN_PROCESS_SCHEDULER=true` |
| 本番（Vercel） | Vercel Cron が下記 URL を叩く              | `vercel.json`                      |

Vercel はリクエスト単位で関数を起動し常駐プロセスを持てないため、アプリ内に常駐スケジューラを置けない。
一方ローカルは常駐できるので、アプリ内スケジューラで同じ生成処理を呼ぶ。

**発火時刻の定義は `vercel.json` の `crons` だけ**。アプリ内スケジューラはそこから cron 式を読んで登録するので、
時刻を変えるときは `vercel.json` だけを直せばローカルにも反映される。

| エンドポイント              | cron 式（UTC） | 実際の発火（JST）               |
| --------------------------- | -------------- | ------------------------------- |
| `/api/cron/summary/weekly`  | `0 15 * * 0`   | **毎週月曜 00:00**              |
| `/api/cron/summary/monthly` | `30 0 1 * *`   | 毎月 1 日 09:30（前月分を生成） |

週次の要件は「JST の月曜 0 時」。
**Vercel Cron は常に UTC で解釈する**ため、cron 式は 9 時間戻して日曜 15:00 UTC と書いてある。
式だけ見ると日曜に見えるが、JST では月曜 0 時になる。UTC の曜日に合わせて直さないこと。

`Authorization: Bearer <CRON_SECRET>` が一致しないリクエストは 401 で弾く。
Vercel はこのヘッダを自動で付与する。

同じ回が重複起動されても二重生成・メール二重送信が起きないよう、
直近 12 時間以内に同じ種別のサマリーが作られていればその実行は何もしない。

手動で叩く場合:

```
curl -H "Authorization: Bearer $CRON_SECRET" https://<your-app>/api/cron/summary/weekly
```

## デプロイ

Vercel Hobby + MongoDB Atlas Free で動かす。

- エントリーポイントは `wsgi.py` のトップレベル変数 `app`
- Python のバージョンは `.python-version` で 3.12 に固定
- cron と関数のバンドル対象は `vercel.json` で指定
- `.env` の内容は Vercel の環境変数に登録する

Vercel Hobby の cron は 1 日 1 回以下の頻度しか設定できず、起動時刻は指定した時間内で最大 59 分ずれる。
週次・月次はこの制約に収まる。

## ディレクトリ構成

このアプリケーションのディレクトリ構成は以下のようになっています：

- `app/`: アプリケーションのルートディレクトリです。
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
- `docker/`: Docker 関連のファイルが配置されるディレクトリです。
- `docker-compose.yml`: Docker Compose ファイルです。
- `scripts/`: 運用・移行用のスクリプトが配置されるディレクトリです。
- `requirements.txt`: アプリケーションが依存する Python パッケージのリストが含まれます。
- `wsgi.py`: アプリケーションを組み立てるエントリーポイントです。デプロイ先はこのファイルを読み込みます。
- `run.py`: ローカル開発用の起動スクリプトです。
- `vercel.json`: デプロイ先の cron とバンドル対象の設定です。
- `.python-version`: デプロイ先で使う Python のバージョンです。
