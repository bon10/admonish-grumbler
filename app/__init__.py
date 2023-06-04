import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

from app.conifg import Config

load_dotenv(override=True)

app = Flask(__name__)
app.config.from_object(Config)

bcrypt = Bcrypt(app)
print(os.getenv('MONGO_URI'))

mongo = MongoClient(os.getenv('MONGO_URI'))

from app.interface.http.user_controller import bp as user_bp

app.register_blueprint(user_bp)

from app import domain, infrastructure, interface, usecase
