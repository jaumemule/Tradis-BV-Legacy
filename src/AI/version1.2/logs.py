import logging
import time
import os


class Log(object):

    def __init__(self):
        logging.basicConfig(level=logging.INFO, filename=os.path.join("logs", time.strftime("run-%Y-%m-%d.log")))

    @staticmethod
    def print(message):
        logging.info(message)

    @staticmethod
    def close():
        logging.shutdown()
