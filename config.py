from os import environ
import requests
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from requests import RequestException
from retry import retry
from sqlalchemy.exc import OperationalError
from utils.common import logging
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def init_application():
    application = Flask(__name__)
    api_rest = Api(application, prefix=environ["API_BASE_PATH"])
    return application, api_rest


def init_db(app):
    DATABASE_URI = 'postgres+psycopg2://' \
                   f'{environ["DB_USERNAME"]}:' \
                   f'{environ["DB_PASSWORD"]}' \
                   f'@{environ["DB_HOST"]}:' \
                   f'{environ["DB_PORT"]}' \
                   f'/{environ["DB_SCHEMA"]}'
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    db.init_app(app)


    return db


@retry(OperationalError, tries=3, delay=2, backoff=2, logger=logger)
def check_db_connection():
    logger.warning("DB Connection Was Initiated")
    db.create_all()


@retry((RequestException, ConnectionError), tries=3, delay=2, backoff=2, logger=logger)
def connect_to_gateway():
    url = environ["GATEWAY_URL"]
    payload = {"serviceType": "users",
               "url": f'http://{environ["API_HOST"]}:{environ["API_PORT"]}{environ["API_BASE_PATH"]}'}
    g_request = requests.post(url, payload)
    if g_request.status_code == 200:
        logger.warning(f"Gateway Connection Established ...")
    else:
        raise ConnectionError(f"Gateway returned status: {g_request.status_code}")
    return g_request.status_code





def get_limiter(app):
    # defined rate limit for entire api
    rate_limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=[environ["DEFAULT_RATE_LIMIT"]]
    )
    return rate_limiter


if __name__ == 'config':
    app, api = init_application()
    db = init_db(app)
    limiter = get_limiter(app)
    ma_serializable = Marshmallow(app)
