from flask import Flask
from flask_restful import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from requests import RequestException
from retry import retry
from sqlalchemy.exc import OperationalError
import os
import logging
import requests

logging.basicConfig(format='%(asctime)-15s -%(process)d-%(levelname)s-%(message)s')

logger = logging.getLogger('config')


def get_env_variable():
    return {
        "DB_USERNAME": os.environ.get('DB_USERNAME'),
        "DB_PASSWORD": os.environ.get('DB_PASSWORD'),
        "DB_HOST": os.environ.get('DB_HOST'),
        "DB_PORT": os.environ.get('DB_PORT'),
        "DB_SCHEMA": os.environ.get('DB_SCHEMA'),
        "API_PORT": os.environ.get('API_PORT'),
        "API_HOST": os.environ.get('API_HOST'),
        "API_BASE_PATH": os.environ.get('API_BASE_PATH'),
        "DEFAULT_RATE_LIMIT": os.environ.get('DEFAULT_RATE_LIMIT'),
        "DEFAULT_CAPACITY": os.environ.get('DEFAULT_CAPACITY'),
        "GATEWAY_URL": os.environ.get('GATEWAY_URL')
    }


def init_application():
    application = Flask(__name__)
    api_rest = Api(application, prefix=env_args["API_BASE_PATH"])
    return application, api_rest


def init_db(app):
    DATABASE_URI = 'postgres+psycopg2://' \
                   f'{env_args["DB_USERNAME"]}:' \
                   f'{env_args["DB_PASSWORD"]}' \
                   f'@{env_args["DB_HOST"]}:' \
                   f'{env_args["DB_PORT"]}' \
                   f'/{env_args["DB_SCHEMA"]}'
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    db.init_app(app)
    return db


@retry(OperationalError, tries=3, delay=2, backoff=2, logger=logger)
def check_db_connection():
    db.create_all()


@retry((RequestException, ConnectionError), tries=3, delay=2, backoff=2, logger=logger)
def connect_to_gateway():
    url = env_args["GATEWAY_URL"]
    payload = {"serviceType": "users",
               "url": f'http://{env_args["API_HOST"]}:{env_args["API_PORT"]}{env_args["API_BASE_PATH"]}'}
    g_request = requests.post(url, payload)
    print(f"Gateway Connection Established ...")
    return g_request.status_code


def get_limiter(app):
    # defined rate limit for entire api
    rate_limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=[env_args["DEFAULT_RATE_LIMIT"]]
    )
    return rate_limiter


if __name__ == 'config':
    env_args = get_env_variable()
    app, api = init_application()
    db = init_db(app)
    limiter = get_limiter(app)
    ma_serializable = Marshmallow(app)
