import logging
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# create_app()内のログが表示されるよう、先にlogging設定を行う
if os.environ.get('FLASK_DEBUG') == 'false':
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

from app import create_app

app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
