import pika


class BrokerConfiguration:
    def __init__(self, host, port, user, pswd, q_names_list, exchange):
        """

        :param host: RabbitMq Host Name
        :param port: RabbitMq Port Number
        :param user: RabbitMq User Name
        :param pswd: RabbitMq User Password
        :param q_names_list: Array of Queue names that will be used for sending messages
        :param exchange: RabbitMq Exchange Name
        """
        self.q_names_list = q_names_list
        self.host = host
        self.port = port
        self.exchange = exchange
        self.credentials = pika.PlainCredentials(user, pswd)

    def get_connection(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      port=self.port,
                                      credentials=self.credentials,
                                      connection_attempts=3,
                                      retry_delay=2))
        return connection

