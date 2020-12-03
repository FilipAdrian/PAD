import pika


def callback(ch, method, properties, body):
    print("Message was received %r" % body)


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

    def consumer(self, q_name):
        """

        :param q_name: Queue Name that will be consumed
        :return: None
        """
        self._channel.basic_consume(
            queue=q_name,
            on_message_callback=callback,
            auto_ack=True
        )

        self._channel.start_consuming()
