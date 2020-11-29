import logging


def callback(ch,method, properties, body):
    print("Message was received %r" % body)


class Consumer:
    logger = logging.getLogger(__name__)

    def __init__(self, config):
        """
        :param config: Object of type BrokerConfiguration
        """
        self._config = config
        self.connection = self._config.get_connection()
        self._channel = self.connection.channel()
        for q_name in self._config.q_names_list:
            self._channel.queue_declare(queue=q_name, durable=True)

    def start_consumer(self, q_name):
        self._channel.basic_consume(
            queue=q_name,
            on_message_callback=callback,
            auto_ack=True
        )

        self._channel.start_consuming()
