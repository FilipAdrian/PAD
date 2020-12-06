from os import environ

import pika

import message_broker.transaction as transaction
from utils.common import logging

logging.getLogger("pika").propagate = False
logger = logging.getLogger(__name__)


def get_message_broker():
    broker = MessageBroker(environ["RABBITMQ_HOST"], environ["RABBITMQ_PORT"],
                           environ["RABBITMQ_USER"], environ["RABBITMQ_PASSWORD"], '')
    logger.warning("Connection To Message Broker Was Initiated")
    broker.init_qs([environ["ORDER_Q_NAME"],
                    environ["PRODUCT_COMPENSATION_Q_NAME"],
                    environ["PRODUCT_Q_NAME"],
                    environ["ORDER_COMPENSATION_Q_NAME"]])
    return broker


class MessageBroker:
    def __init__(self, host, port, user, pswd, exchange):
        """

        :param host: RabbitMq Host Name
        :param port: RabbitMq Port Number
        :param user: RabbitMq User Name
        :param pswd: RabbitMq User Password
        :param exchange: RabbitMq Exchange Name
        """
        self.host = host
        self.port = port
        self.exchange = exchange
        self.credentials = pika.PlainCredentials(user, pswd)

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      port=self.port,
                                      credentials=self.credentials,
                                      connection_attempts=3,
                                      retry_delay=2))
        self._channel = self.connection.channel()

    def init_qs(self, q_names_list):
        """

        :param q_names_list: Array of Queue names which will be initialized for sending or consuming messages
        :return: None
        """
        for q_name in q_names_list:
            self._channel.queue_declare(queue=q_name, durable=True)

    def close_connection(self):
        self.connection.close()

    def publish(self, q_name, payload):
        """

        :param q_name: Queue Name where payload will be redirected
        :param payload: Json Payload
        :return: None
        """

        self._channel.basic_publish(
            exchange=self.exchange,
            routing_key=q_name,
            body=payload)

    def consume(self, q_name):
        """

        :param q_name: Queue Name that will be consumed
        :return: None
        """

        def callback(ch, method, properties, body):
            transaction.process_transaction(body, self)

        self._channel.basic_consume(
            queue=q_name,
            on_message_callback=callback,
            auto_ack=True
        )

        self._channel.start_consuming()
