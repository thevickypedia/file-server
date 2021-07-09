from base64 import b64encode, b64decode
from binascii import Error
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from inspect import currentframe
from logging import getLogger, FileHandler, INFO, Formatter, StreamHandler
from os import environ, path, getcwd, listdir, makedirs, rename
from pathlib import PurePath
from socket import gethostbyname
from ssl import wrap_socket
from time import time

from yaml import load, dump, FullLoader


# noinspection PyPep8Naming
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

        Overwrites the base method: `BaseHTTPRequestHandler.log_message()`

        Args:
            format_: String operator %s
            *args: Logs from SimpleHTTPRequestHandler displaying request method type and HTTP status code.

        """
        if len(args) == 3:  # We don't have to care about NOT FOUND items because they are mostly hidden/protected.
            method, status_code, ignore = args  # ignore always returns `-`
            method = str(method).split('/')[0].strip()
            if int(str(status_code).strip()) == 200:
                fileLogger.info(f'Received {status_code} while accessing a {method} method to reach {self.path}')
            else:
                fileLogger.error(f'Received {status_code} while accessing a {method} method to reach {self.path}')

    def do_HEAD(self) -> None:
        """Sends 200 response and sends headers when authentication is successful."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self) -> None:
        """Serve a front end with user authentication."""
        global authenticated
        if reset_auth() and 'Authorization' in self.headers.keys():
            consoleLogger.warning('Authorized via stored cookies. However session expired, so headers have been reset.')
            self.headers.replace_header('Authorization', None)
            self.disable_cache()

        if not (auth_header := self.headers.get("Authorization")):
            self.do_AUTH()
            if not authenticated:
                self.wfile.write(login_failed.encode(encoding='UTF-8'))
            else:
                self.wfile.write(session_expiry.encode(encoding='UTF-8'))
        elif auth_header == "Basic " + self._auth:
            target_path = host_dir + self.path
            if path.isdir(target_path) and 'index.html' in listdir(target_path):
                old_name = target_path + 'index.html'
                new_name = target_path + 'index_TEMP.html'
                consoleLogger.critical(f'Renaming {old_name} to {new_name}')
                rename(old_name, new_name)
                renamed.append({old_name: new_name})
            if not authenticated and self.path == '/':
                self.path = getcwd().replace(host_dir, "") + path.sep + 'auth_server.html'
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except BrokenPipeError:
                consoleLogger.error(f'Received BrokenPipeError while reaching {self.path}')
            authenticated = True
        else:
            self.do_AUTH()
            auth = auth_header.strip('Basic ')
            try:
                auth = b64decode(auth).decode().split(':')
                consoleLogger.error(f'Authentication Blocked: Username: {auth[0]}\tPassword: {auth[1]}')
            except Error:
                consoleLogger.error(f'Authentication Blocked: Encoded: {auth}')

    def do_AUTH(self) -> None:
        """Sends headers to authenticate the requester."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Test"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self) -> None:
        """Handles POST request and writes the received data into a yaml file."""
        length = int(self.headers.get('content-length'))
        peanut = self.rfile.read(length)
        butter = peanut.decode(encoding='UTF-8').split('&')[0]
        client_info = load(butter, Loader=FullLoader)
        rootLogger.fatal(str(client_info).replace("'", "").lstrip('{').rstrip('}'))
        current_time = f"Server Datetime: {(datetime.now()).strftime('%B %d, %Y %I:%M %p')}"
        hashes = ''.join(['#' for _ in range(74)])
        with open('client_info.yaml', 'w') as client:
            client.write(f"{hashes}\n#\t\t\t\t{current_time}\n{hashes}\n")
            dump(client_info, client, indent=4)

    def disable_cache(self) -> None:
        """Headers to force no-cache and site-data to expire."""
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


def server_function(flag: bool) -> None:
    """Uses local certificate from ~.ssh to serve the page as https if flag is set to True.

    Args:
        flag: Whether or not to wrap the socket with the certificate.

    """
    rootLogger.info('Initiating file server.')
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=username,
        password=password,
        directory=host_dir
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
        [(rename(new_name, old_name), consoleLogger.critical(f'Reverted {new_name} to {old_name}')) for each in renamed
         for old_name, new_name in each.items() if renamed]  # cheat to two operations within list comprehension = tuple
        rootLogger.info('Terminating file server.')
        server.server_close()
        server.shutdown()
        print(f"{line_number()} - File server has been terminated.")


def line_number() -> int:
    """Uses the inspect module to fetch the line number from current frame.

    Returns:
        Line number of where this function is called.

    """
    return currentframe().f_back.f_lineno


def logging_wrapper() -> tuple:
    """Wraps logging module to create multiple handlers for different purposes.

    Notes:
        - fileLogger: Writes the log information only to the log file.
        - consoleLogger: Writes the log information only in stdout.
        - rootLogger: Logs the entry in both stdout and log file.

    Returns:
        A tuple of classes logging.Logger for file, console and root logging.

    """
    makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
    log_file = datetime.now().strftime('logs' + path.sep + 'auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    log_formatter = Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
        datefmt='%b-%d-%Y %H:%M:%S'
    )

    file_logger = getLogger('FILE')
    console_logger = getLogger('CONSOLE')
    root_logger = getLogger(PurePath(__file__).stem)

    file_handler = FileHandler(filename=log_file)
    file_handler.setFormatter(fmt=log_formatter)
    file_logger.setLevel(level=INFO)
    file_logger.addHandler(hdlr=file_handler)

    console_handler = StreamHandler()
    console_handler.setFormatter(fmt=log_formatter)
    console_logger.setLevel(level=INFO)
    console_logger.addHandler(hdlr=console_handler)

    root_logger.addHandler(hdlr=file_handler)
    root_logger.addHandler(hdlr=console_handler)
    return file_logger, console_logger, root_logger


if __name__ == "__main__":
    if not (username := environ.get('username')) or not (password := environ.get('password')):
        exit('Add username and password in local ENV VARS to proceed.')

    fileLogger, consoleLogger, rootLogger = logging_wrapper()

    with open('session.html', 'r') as file:
        session_expiry = file.read()

    with open('no_auth.html', 'r') as file:
        login_failed = file.read()

    start_time = time()  # set to the current time to reset the auth headers when timeout is reached
    first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
    authenticated = False  # set to False to write the appropriate message in the HTML file
    renamed = []  # set to empty list to append dictionaries with re-namings done for index.html

    home_dir = path.expanduser('~')
    if not (host_dir := environ.get('directory')):
        host_dir = home_dir

    ssh_dir = home_dir + path.sep + path.join('.ssh')
    makedirs(ssh_dir) if '.ssh' not in listdir(home_dir) else None
    cert_file = path.expanduser(ssh_dir) + path.sep + "cert.pem"
    key_file = path.expanduser(ssh_dir) + path.sep + "key.pem"

    if 'cert.pem' in listdir(ssh_dir) and 'key.pem' in listdir(ssh_dir):
        server_function(flag=True)
    else:
        rootLogger.warning(
            f"Run the following command in a terminal at {ssh_dir} to create a private certificate."
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
            f"openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout {key_file} -out {cert_file}"
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
        )
        server_function(flag=False)
