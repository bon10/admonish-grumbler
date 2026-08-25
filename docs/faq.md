# FAQ

開発中に詰まりやすい点と対処。

## コンテナ起動時にパッケージのインストールが失敗する

```
ERROR: Ignored the following versions that require a different python version: ...
ERROR: No matching distribution found for ...
```

依存パッケージは名前付きボリューム `admonish-grumbler_venv` に入っていて、コンテナを作り直しても残る。
イメージの Python バージョンを変えても、ボリューム内の venv は古いバージョンのまま残るため食い違う。

`docker compose up` はイメージを再ビルドしないので、ボリュームとイメージの両方を作り直す。

```
% docker compose down
% docker volume rm admonish-grumbler_venv
% docker compose up -d --build
```

## `scripts/` のスクリプトが `ModuleNotFoundError` になる

```
ModuleNotFoundError: No module named 'flask_bcrypt'
```

依存パッケージはホストではなくコンテナ側の venv に入っている。コンテナ内で実行する。

```
% docker exec -it admonish-grumbler-app python scripts/generate_password_hash.py
```

## `http://localhost:5000/` が 403 を返す

macOS の AirPlay レシーバーがポート 5000 を使っている。アプリの応答ではない。

```
% lsof -nP -iTCP:5000 -sTCP:LISTEN
ControlCe  ...  TCP *:5000 (LISTEN)
```

このアプリはコンテナのポートを `5500:5000` で公開しているので、ブラウザからは
`http://localhost:5500` を使う。ホスト側で直接 `run.py` を動かしたい場合は、
システム設定 → 一般 → AirDrop と Handoff → AirPlay レシーバー をオフにする。

## 週次サマリーの cron 式が日曜になっているが正しいのか

正しい。要件は「JST の月曜 0 時」で、Vercel Cron は常に UTC で解釈するため、
9 時間戻した `0 15 * * 0`（日曜 15:00 UTC）が JST の月曜 0 時にあたる。
UTC の曜日に合わせて `* * 1` に直すと 1 日ずれる。

## Vercel のプレビュー URL が `vercel.com/sso-api` にリダイレクトされる

Vercel の Deployment Protection によるもので、アプリの異常ではない。
Vercel にログインしたブラウザからアクセスすれば開ける。

Hobby プランでは本番ドメインは保護対象外で公開される。本番を守るのはアプリ側のログインと
`CRON_SECRET` になる。

## 環境変数を変えたのに Vercel に反映されない

環境変数の変更は既存のデプロイには遡及しない。登録・変更したあとに再デプロイする。
