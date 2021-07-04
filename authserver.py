from base64 import b64encode, b64decode
from datetime import datetime
from functools import partial
# noinspection PyUnresolvedReferences
from http.server import SimpleHTTPRequestHandler, test
from logging import getLogger, basicConfig, INFO
from os import environ, path, getcwd, listdir, makedirs
from pathlib import PurePath
from socket import gethostbyname


class AuthHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Main class to present webpages and authentication.

    >>> AuthHTTPRequestHandler

    """

    def __init__(self, *args: tuple, **kwargs: dict):
        """Gets the authentication details from the user and encodes it.

        Args:
            *args: Socket generated using IP address and Port.
            **kwargs: Dictionary with key-value pairs of username, password and directory to serve.
        """
        self.allow_reuse_address = True
        username = kwargs.pop("username")
        password = kwargs.pop("password")
        self._auth = b64encode(f"{username}:{password}".encode()).decode()
        super().__init__(*args, **kwargs)

    def log_message(self, format_: str, *args: tuple) -> None:
        """Suppresses logs from http.server by holding the args.

        Args:
            format_: String operator %s
            *args: Logs from SimpleHTTPRequestHandler displaying request method type and HTTP status code.

        """
        method, status_code, ignore = args  # ignore always returns `-`
        method = str(method).split('/')[0].strip()
        logger.info(f'Received {status_code} while accessing a {method} method to reach {self.path}')

    def do_HEAD(self) -> None:
        """Sends 200 response and sends headers when authentication is successful."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    # noinspection PyPep8Naming,SpellCheckingInspection
    def do_AUTHHEAD(self) -> None:
        """Sends 401 response and sends headers when authentication wasn't done or unsuccessful."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Test"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self) -> None:
        """Serve a front end with user authentication."""
        if not self.headers.get("Authorization"):
            logger.warning('No authentication was received.')
            self.do_AUTHHEAD()
            self.wfile.write(b"No auth header received")
        elif self.headers.get("Authorization") == "Basic " + self._auth:
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            auth = b64decode(self.headers.get('Authorization').strip('Basic ')).decode().split(':')
            logger.info(f'Authentication Blocked: Username: {auth[0]}\tPassword: {auth[1]}')
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get("Authorization").encode())
            self.wfile.write(b"Not authenticated")


if __name__ == "__main__":
    makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
    LOG_FILENAME = datetime.now().strftime('logs/auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    basicConfig(
        filename=LOG_FILENAME, level=INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
        datefmt='%b-%d-%Y %H:%M:%S'
    )
    logger = getLogger(PurePath(__file__).stem)  # gets current file name
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=environ.get('username'),
        password=environ.get('password'),
        directory=path.expanduser('~')
    )
    logger.info('Starting Auth Server.')
    test(HandlerClass=handler_class, port=environ.get('port', 1234), bind=gethostbyname('localhost'))
