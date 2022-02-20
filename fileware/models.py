import os
from datetime import datetime


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
        "disable_existing_loggers": False,
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
