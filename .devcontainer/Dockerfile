# Pythonイメージをベースにする
FROM python:3.8

# ワーキングディレクトリを設定
WORKDIR /app

# 仮想環境のセットアップ
RUN python -m venv /venv

# 仮想環境をアクティベートする
ENV PATH="/venv/bin:$PATH"

# 依存関係をインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# ポート5000を公開
EXPOSE 5000

# アプリケーションを起動
#CMD ["python", "run.py"]
