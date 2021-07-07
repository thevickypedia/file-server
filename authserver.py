from base64 import b64encode, b64decode
from binascii import Error
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from inspect import currentframe
from logging import getLogger, basicConfig, INFO
from os import environ, path, getcwd, listdir, makedirs
from pathlib import PurePath
from socket import gethostbyname
from ssl import wrap_socket
from time import time


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
        if len(args) == 3:  # We don't have to care about NOT FOUND items because they are mostly hidden/protected.
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
        global authenticated
        if reset_auth() and 'Authorization' in self.headers.keys():
            logger.error('Authorized from stored cookies. However the session has expired, so headers have been reset.')
            self.headers.replace_header('Authorization', None)
            self.disable_cache()

        if not (auth_header := self.headers.get("Authorization")):
            self.do_AUTHHEAD()
            if not authenticated:
                logger.warning('No authentication was received.')
                self.wfile.write(
                    b"""<!DOCTYPE html><html><head><style>img {display: block;margin-left: auto;margin-right: auto;}
                    </style></head><body><h2 style="text-align:center">LOGIN FAILED</h2><h4 style="text-align:center">
                    User error - Replace user</h4><p>
                    <img border="0"src="https://vigneshrao.com/error_img/Preloader_3.gif" width="200" height="200"
                    alt="loader"class="center"></p></body></html>"""
                )
            else:
                logger.warning('Session has expired.')
                self.wfile.write(
                    """<!DOCTYPE html><html><head><style>img {display: block;margin-left: auto;margin-right: auto;}
                    </style></head><body><h2 style="text-align:center">SESSION EXPIRED</h2><h4 style="text-align:center"
                    >Authentication doesn't last forever.</h4><p>
                    <img border="0"src="https://vigneshrao.com/error_img/Preloader_3.gif" width="200" height="200"
                    alt="loader"class="center"></p></body></html>""".encode()
                )
        elif auth_header == "Basic " + self._auth:
            authenticated = True
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except BrokenPipeError:
                logger.error(f'Received BrokenPipeError while reaching {self.path}')
        else:
            self.do_AUTHHEAD()
            auth = auth_header.strip('Basic ')
            try:
                auth = b64decode(auth).decode().split(':')
                logger.error(f'Authentication Blocked: Username: {auth[0]}\tPassword: {auth[1]}')
            except Error:
                logger.error(f'Authentication Blocked: Encoded: {auth}')
            self.wfile.write(b"Not authenticated") if not authenticated else self.wfile.write(b"Session Expired")

    def disable_cache(self) -> None:
        if 'Cache-Control' in self.headers.keys():
            self.headers.replace_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        else:
            self.headers.add_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        self.headers.add_header(_name='Pragma', _value='no-cache')
        self.headers.add_header(_name='Expires', _value='0')
        self.headers.add_header(_name='Clear-Site-Data', _value='"cache", "cookies", "storage", "executionContexts"')


def reset_auth():
    """Tells if the authentication header has to be reset and cache to be cleared.

    Notes:
        Note that if an authentication is done at the end of 15 minutes, there will be a re-auth prompted.

    Returns:
        - True when it has been more than 15 minutes since the first/previous expiry.
        - None when not.

    """
    global start_time, first_run
    if first_run:
        first_run = False
        return True
    elif time() - start_time > 900:
        start_time = time()
        return True


def serve_https(flag: bool) -> None:
    """Uses local certificate from ~.ssh to serve the page as https if flag is set to True.

    Args:
        flag: Whether or not to wrap the socket with the certificate.

    """
    logger.info('Initiating file server.')
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=username,
        password=password,
        directory=path.expanduser('~')
    )
    server = HTTPServer(server_address=('localhost', int(environ.get('port', 4443))), RequestHandlerClass=handler_class)

    if flag:
        server.socket = wrap_socket(sock=server.socket, server_side=True, certfile=cert_file, keyfile=key_file)
        endpoint = f"https://{gethostbyname('localhost')}:{server.server_port}"
    else:
        endpoint = f"http://{gethostbyname('localhost')}:{server.server_port}"
    print(f"{line_number()} - Serving at: {endpoint}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Terminating file server.')
        server.server_close()
        server.shutdown()
        print(f"{line_number()} - File server has been terminated.")


def line_number() -> int:
    """Returns the line number of where this function is called."""
    return currentframe().f_back.f_lineno


if __name__ == "__main__":
    if not (username := environ.get('username')) or not (password := environ.get('password')):
        exit('Add username and password in local ENV VARS to proceed.')

    makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
    LOG_FILENAME = datetime.now().strftime('logs' + path.sep + 'auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    basicConfig(
        filename=LOG_FILENAME, level=INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
        datefmt='%b-%d-%Y %H:%M:%S'
    )
    logger = getLogger(PurePath(__file__).stem)  # gets current file name

    start_time = time()  # set to the current time to reset the auth headers when timeout is reached
    first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
    authenticated = False  # set to False to write the appropriate message in the HTML file

    ssh_dir = path.expanduser('~') + path.sep + path.join('.ssh')
    makedirs(ssh_dir) if '.ssh' not in listdir(path.expanduser('~')) else None
    cert_file = path.expanduser(ssh_dir) + path.sep + "cert.pem"
    key_file = path.expanduser(ssh_dir) + path.sep + "key.pem"

    if 'cert.pem' in listdir(ssh_dir) and 'key.pem' in listdir(ssh_dir):
        serve_https(flag=True)
    else:
        logger.warning(
            f"{line_number()} - Run the following command in a terminal at {ssh_dir} to create a private certificate."
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
            f"openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout {key_file} -out {cert_file}"
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
        )
        serve_https(flag=False)
