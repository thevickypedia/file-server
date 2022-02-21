import logging.config
import os
from datetime import datetime
from pathlib import Path

os.makedirs('logs') if not os.path.isdir('logs') else None


def server_logger():
    """Creates a log file for server logs and configures the logging config for server logger.

    Returns:
        logging.Logger:
        Returns logger config for server.
    """
    if not os.path.isfile(LogConfig.SERVER_LOG_FILE):
        Path(LogConfig.SERVER_LOG_FILE).touch()

    logging.config.dictConfig(config=LogConfig.LOGGING_CONFIG)
    return logging.getLogger('server')


def ngrok_logger() -> logging.Logger:
    """Creates a log file for ngrok logs and configures the logging config for ngrok logger.

    Returns:
        logging.Logger:
        Returns logger config for ngrok.
    """
    if not os.path.isfile(LogConfig.TUNNEL_LOG_FILE):
        Path(LogConfig.TUNNEL_LOG_FILE).touch()

    logging.config.dictConfig(config=LogConfig.LOGGING_CONFIG)
    return logging.getLogger('tunnel')


class LogConfig:
    """Custom log configuration.

    >>> LogConfig

    """

    LOG_LEVEL = "DEBUG"

    SERVER_LOG_FILE = datetime.now().strftime('logs' + os.path.sep + 'fileserver_%m_%d_%Y.log')
    TUNNEL_LOG_FILE = datetime.now().strftime('logs' + os.path.sep + 'tunnel_%m_%d_%Y.log')

    FILE_LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "server": {
                "format": FILE_LOG_FORMAT,
                "filename": SERVER_LOG_FILE,
                "datefmt": "%b %d, %Y %H:%M:%S"
            },
            "tunnel": {
                "format": FILE_LOG_FORMAT,
                "filename": TUNNEL_LOG_FILE,
                "datefmt": "%b %d, %Y %H:%M:%S"
            }
        },
        "handlers": {
            "server": {
                "formatter": "server",
                "class": "logging.FileHandler",
                "filename": SERVER_LOG_FILE,
            },
            "tunnel": {
                "formatter": "tunnel",
                "class": "logging.FileHandler",
                "filename": TUNNEL_LOG_FILE,
            }
        },
        "loggers": {
            "server": {"handlers": ["server"], "level": LOG_LEVEL, "filename": SERVER_LOG_FILE},
            "tunnel": {"handlers": ["tunnel"], "level": LOG_LEVEL, "filename": TUNNEL_LOG_FILE}
        }
    }
