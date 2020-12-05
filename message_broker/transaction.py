import json
from os import environ

from werkzeug import exceptions

import resources.user as user
from utils.common import logging

logger = logging.getLogger(__name__)


def process_transaction(body, broker):
    """
        :param body: Json Payload
        {
            "transaction_id": "cf2c9f1d-1ce3-415e-86ab-ee274b94f272",
            "user_id": 3,
            "total_price": 25.2,
            "products":[
                    {
                        "product_id": 3,
                        "product_name": "Wheel",
                        "amount":2
                    }
            ]
        }
        
        :param broker: object of MessageBroker class
    """
    payload = json.loads(body)
    logger.info("Start Transaction", extra={"transaction_id": payload["transaction_id"]})

    logger.debug("Message was received %r" % payload)
    try:
        current_user = user.get_user_by_id(payload["user_id"])
        diff = current_user.money_amount - payload["total_price"]
        logger.info("Difference: " + str(diff))
        if diff < 0:
            logger.error(f"Not Enough Money, for user id: %r" % payload["user_id"],
                         extra={"transaction_id": payload["transaction_id"]})
            payload["error_msg"] = "Not Enough Money"
            send_compensation_msg(broker, payload)
        else:
            current_user.money_amount = diff
            user.update(current_user)
            broker.publish(environ["ORDER_Q_NAME"], body)
            logger.info("Money were extracted from account", extra={"transaction_id": payload["transaction_id"]})


    except exceptions.NotFound:
        logger.error(f"User with id: %r Not Found" % payload["user_id"],
                     extra={"transaction_id": payload["transaction_id"]})
        payload["error_msg"] = "User not found"
        send_compensation_msg(broker, payload)

    logger.info("End Transaction", extra={"transaction_id": payload["transaction_id"]})


def send_compensation_msg(broker, body):
    payload = json.dumps(body)
    broker.publish(environ["PRODUCT_COMPENSATION_Q_NAME"], payload)
    broker.publish(environ["ORDER_COMPENSATION_Q_NAME"], payload)
