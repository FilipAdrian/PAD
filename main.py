
from config import api, app, check_db_connection, connect_to_gateway
from message_broker.broker import get_message_broker
from resources.user import User, Users
from threading import Thread
from os import environ
# Add API resources
api.add_resource(Users, "/users", endpoint="users")
api.add_resource(User, "/users/<int:user_id>", endpoint="user-by-id")


# broker.consume(env_args["PRODUCT_Q_NAME"])


if __name__ == "__main__":
    broker = get_message_broker()
    thread = Thread(target=broker.consume, args=(environ["PRODUCT_Q_NAME"], ))
    thread.start()
    connect_to_gateway()
    check_db_connection()
    app.run(host=environ["API_HOST"], port=environ["API_PORT"], debug=True,
            threaded=True)  # Set up sever host,port enabled debug mode

