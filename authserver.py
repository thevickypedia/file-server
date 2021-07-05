from base64 import b64encode, b64decode
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from inspect import currentframe
from logging import getLogger, basicConfig, INFO
from os import environ, path, getcwd, listdir, makedirs
from pathlib import PurePath
from socket import gethostbyname
from ssl import wrap_socket


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
        self._auth = b64encode(f"{kwargs.pop('username')}:{kwargs.pop('password')}".encode()).decode()
        super().__init__(*args, **kwargs)

    def log_message(self, format_: str, *args: tuple) -> None:
        """Suppresses logs from http.server by holding the args.

        Args:
            format_: String operator %s
            *args: Logs from SimpleHTTPRequestHandler displaying request method type and HTTP status code.

        """
        if 'HTTPStatus.NOT_FOUND' not in str(args):
            method, status_code, ignore = args  # ignore always returns `-`
            method = str(method).split('/')[0].strip()
            if int(str(status_code).strip()) == 200:
                logger.info(f'Received {status_code} while accessing a {method} method to reach {self.path}')
            else:
                logger.error(f'Received {status_code} while accessing a {method} method to reach {self.path}')

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
        if 'Cache-Control' in self.headers.keys():
            self.headers.replace_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        else:
            self.headers.add_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        self.headers.add_header(_name='Pragma', _value='no-cache')
        self.headers.add_header(_name='Expires', _value='0')
        self.headers.add_header(_name='Clear-Site-Data', _value='"cache", "cookies", "storage", "executionContexts"')
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


def serve_https() -> None:
    """Uses local certificate from ~/.ssh to serve the page as https"""
    logger.info('Initiating HTTPS server.')
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=username,
        password=password,
        directory=path.expanduser('~')
    )
    https = HTTPServer(server_address=('localhost', int(environ.get('port', 4443))), RequestHandlerClass=handler_class)
    https.socket = wrap_socket(sock=https.socket, server_side=True, certfile=cert_file, keyfile=key_file)
    print(f"{line_number()} - Serving at: https://{gethostbyname('localhost')}:{https.server_port}")
    try:
        https.serve_forever()
    except KeyboardInterrupt:
        https.shutdown()
        print(f"{line_number()} - File server has been terminated.")


def line_number():
    """Returns the line number of where this function is called."""
    return currentframe().f_back.f_lineno


if __name__ == "__main__":
    if not (username := environ.get('username')) or not (password := environ.get('password')):
        exit('Add username and password in local ENV VARS to proceed.')

    ssh_dir = path.expanduser('~/.ssh')
    makedirs(ssh_dir) if '.ssh' not in listdir(path.expanduser('~')) else None
    cert_file = path.expanduser(f"{ssh_dir}/cert.pem")
    key_file = path.expanduser(f"{ssh_dir}/key.pem")
    if 'cert.pem' not in listdir(ssh_dir) or 'key.pem' not in listdir(ssh_dir):
        exit(f"{line_number()} - Run the following command in a terminal {ssh_dir} to create a private certificate.\n\n"
             f"openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout {key_file} -out {cert_file}")

    makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
    LOG_FILENAME = datetime.now().strftime('logs/auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    basicConfig(
        filename=LOG_FILENAME, level=INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
        datefmt='%b-%d-%Y %H:%M:%S'
    )
    logger = getLogger(PurePath(__file__).stem)  # gets current file name
    serve_https()
