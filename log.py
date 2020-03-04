import logging

def new_stream_logger(name, level=logging.INFO):
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Use StreamHandler() to log to the console
    handler = logging.StreamHandler()
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # Don't forget to add the stream handler
    logger.addHandler(handler)
    return logger