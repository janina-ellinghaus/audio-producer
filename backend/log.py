import logging


def getLogger(name) -> logging.Logger:
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger(name)
