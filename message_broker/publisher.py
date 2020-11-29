from common.common import logging

class Publisher:
    logger = logging.getLogger(__name__)

    def __init__(self, config):
        """
        :param config: Object of type BrokerConfiguration
        """
        self._config = config
        self.connection = config.get_connection()
        self.channel = self.connection.channel()
        for q_name in self._config.q_names_list:
            self.channel.queue_declare(queue=q_name, durable=True)

    def publish(self, q_name, payload):
        """

        :param q_name: Queue Name where payload will be redirected
        :param payload: Json Payload
        :return: None
        """

        self.channel.basic_publish(
            exchange=self._config.exchange,
            routing_key=q_name,
            body=payload)

    def close_connection(self):
        self.connection.close()
