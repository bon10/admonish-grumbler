# Pythonイメージをベースにする
FROM python:3.9

# ワーキングディレクトリを設定
WORKDIR /app

# 仮想環境のセットアップ（ボリュームマウント後に再作成されるためentrypoint で処理）
ENV PATH="/venv/bin:$PATH"

# 依存関係をインストール
COPY requirements.txt .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

# アプリケーションのソースコードをコピー
COPY . .

# ポート5000を公開
EXPOSE 5000

# アプリケーションを起動
#CMD ["python", "run.py"]
