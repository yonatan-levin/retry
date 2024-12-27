import logging


def getLogger(name, level=logging.INFO, fmt='[%(asctime)s] %(levelname)s:%(name)s: %(message)s'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger