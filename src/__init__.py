from logging import DEBUG, Formatter, getLogger, StreamHandler, WARN


handler = StreamHandler()
handler.setLevel(WARN)

fmt = '%(levelname)-8s: %(asctime)s | %(message)s'
formatter = Formatter(
    fmt,
    datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger = getLogger()
logger.setLevel(DEBUG)
logger.addHandler(handler)
