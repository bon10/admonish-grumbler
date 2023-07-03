import logging
import os

from app import create_app

app = create_app()

if os.environ.get('FLASK_DEBUG') == 'false':
    app.debug = False

if app.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
