"""
ローカル開発用の起動スクリプト。

アプリ本体の組み立ては wsgi.py と共通で、こちらは開発サーバの起動のみを担う。
"""

from wsgi import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
