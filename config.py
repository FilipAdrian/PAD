import logging
import os

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

import message_broker

logger = logging.getLogger(__name__)


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
        "GATEWAY_URL": os.environ.get('GATEWAY_URL'),
        "RABBITMQ_HOST": os.environ.get('RABBITMQ_HOST'),
        "RABBITMQ_PORT": os.environ.get('RABBITMQ_PORT'),
        "RABBITMQ_USER": os.environ.get('RABBITMQ_USER'),
        "RABBITMQ_PASSWORD": os.environ.get('RABBITMQ_PASSWORD'),
        "ORDER_Q_NAME": os.environ.get('ORDER_Q_NAME'),
        "PRODUCT_Q_NAME": os.environ.get('PRODUCT_Q_NAME'),
        "PRODUCT_COMPENSATION_Q_NAME": os.environ.get('PRODUCT_COMPENSATION_Q_NAME'),
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
    logger.warning(f"Gateway Connection Established ...")
    return g_request.status_code


def get_publisher():
    broker_config = message_broker.BrokerConfiguration(env_args["RABBITMQ_HOST"], env_args["RABBITMQ_PORT"],
                                                       env_args["RABBITMQ_USER"], env_args["RABBITMQ_PASSWORD"],
                                                       [env_args["ORDER_Q_NAME"],
                                                        env_args["PRODUCT_COMPENSATION_Q_NAME"]], '')
    logger.warning("Publisher Was Initiated")
    return message_broker.Publisher(broker_config)


def get_consumer():
    broker_config = message_broker.BrokerConfiguration(env_args["RABBITMQ_HOST"], env_args["RABBITMQ_PORT"],
                                                       env_args["RABBITMQ_USER"], env_args["RABBITMQ_PASSWORD"],
                                                       [env_args["PRODUCT_Q_NAME"]], '')
    logger.warning("Consumer Was Initiated")
    return message_broker.Consumer(broker_config)


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
    publisher = get_publisher()
    consumer = get_consumer()
    db = init_db(app)
    limiter = get_limiter(app)
    ma_serializable = Marshmallow(app)
