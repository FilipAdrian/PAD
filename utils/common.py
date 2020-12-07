import logging.config
import os
import random
import string
from envyaml import EnvYAML
from jproperties import Properties

config = Properties()

with open('app-config.properties', 'rb') as config_file:
    config.load(config_file)

with open('log_config.yaml', 'r') as log_config_file:
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_config = EnvYAML("log_config.yaml")
    logging.config.dictConfig(log_config)


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str
