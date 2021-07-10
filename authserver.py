from base64 import b64encode, b64decode
from binascii import Error
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from inspect import currentframe
from logging import getLogger, FileHandler, INFO, Formatter, StreamHandler
from os import environ, path, getcwd, stat, listdir, makedirs, rename
from pathlib import PurePath, Path
from ssl import wrap_socket
from time import time
from urllib.request import urlopen

from yaml import load, dump, FullLoader

from helper_functions.emailer import Emailer
from helper_functions.ngrok_fetcher import get_ngrok


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
            if not authenticated:
                self.do_HEAD()
                self.wfile.write(auth_success.encode(encoding='UTF-8'))
                authenticated = True
                return
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except BrokenPipeError:
                consoleLogger.error(f'Received BrokenPipeError while reaching {self.path}')
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
        global endpoint
        now = datetime.now()
        client_file = 'client_info.yaml'
        length = int(self.headers.get('content-length'))
        peanut = self.rfile.read(length)
        butter = peanut.decode(encoding='UTF-8').split('&')[0]
        client_info = load(butter, Loader=FullLoader)
        if client_info.get('ip') == load(urlopen('https://ipapi.co/json/'), Loader=FullLoader).get('ip'):
            return
        rootLogger.fatal(str(client_info).replace("'", "").lstrip('{').rstrip('}'))

        if path.isfile(client_file):
            with open(client_file, 'r') as client:
                exist = load(''.join([nut for nut in client.readlines() if not nut.startswith('#')]), Loader=FullLoader)

            # avoids duplicate notification for repeated trials in less than 5 minutes
            if int(now.timestamp()) - int(stat(client_file).st_mtime) < 300 and \
                    client_info.get('_html_ref') == exist.get('_html_ref') and \
                    client_info.get('ip') == exist.get('ip'):
                rootLogger.critical(f"{exist.get('ip')} performed {exist.get('_html_ref')} once again within 2 minutes")
                return

        current_time = f"Server Datetime: {now.strftime('%B %d, %Y %I:%M %p')}"
        hashes = ''.join(['#' for _ in range(74)])
        with open(client_file, 'w') as client:
            client.write(f"{hashes}\n#\t\t\t\t{current_time}\n{hashes}\n")
            dump(client_info, client, indent=4)

        if not notify:
            return

        if not (status := client_info.get('_html_ref')):
            status = 'An undefined login attempt'

        if global_endpoint := get_ngrok():
            endpoint = global_endpoint
        else:
            endpoint = endpoint or f"http://{':'.join(map(str, self.connection.getsockname()))}"

        rootLogger.critical(Emailer(
            gmail_user=gmail_user, gmail_pass=gmail_pass, recipient=recipient,
            subject=f"WARNING: {status} was detected. {current_time}", attachment=client_file,
            body=f"A connection with status `{status}` has been made to your personal cloud serving at "
                 f"{endpoint}\n\nDetails of the client are attached. If this was you, you may disregard this email. "
                 f"Otherwise stop the server immediately and rotate your credentials before restarting."
                 f"\n\n\n\n\n\n\n\n\n\n"
                 f"Explore logs: {endpoint}/{(str(base_file).strip(base_file.name) + log_file).strip(host_dir)}"
        ).send_email())

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
        - True if it is the first login attempt or it has been more than 15 minutes since the first/previous expiry.

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
    global endpoint
    rootLogger.info('Initiating file server.')
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=username,
        password=password,
        directory=host_dir
    )
    server = HTTPServer(server_address=('localhost', port), RequestHandlerClass=handler_class)

    if flag:
        server.socket = wrap_socket(sock=server.socket, server_side=True, certfile=cert_file, keyfile=key_file)
        endpoint = f"https://{':'.join(map(str, server.server_address))}"
    else:
        endpoint = f"http://{':'.join(map(str, server.server_address))}"
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


def file_gatherer() -> list:
    """Uses `pathlib.Path(file).read_text()` to read the files.

    Notes:
        Actual way of doing this is to open and read the file individually. But I'm a fan of list comprehensions.
        `auth_success_, login_failed_, session_expiry_ = [open(f'html/{file}').read() for file in listdir('html')]`
        But opening a file in list comprehension leaves the file open through out the code execution.
        This can be verified using `psutil.Process().open_files()`

    Returns:
        Returns the data in each file within the html directory.

    """
    return [Path(f'html/{file}').read_text() for file in listdir('html')]


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
    log_formatter = Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
        datefmt='%b-%d-%Y %H:%M:%S'
    )

    file_logger = getLogger('FILE')
    console_logger = getLogger('CONSOLE')
    root_logger = getLogger(base_file.stem)

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

    default_port = 4443
    port = int(environ.get('port', default_port))

    start_time = time()  # set to the current time to reset the auth headers when timeout is reached
    first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
    authenticated = False  # set to False to write the appropriate message in the HTML file
    renamed = []  # set to empty list to append dictionaries with re-namings done for index.html
    notify = True  # notify is set to true by default unless the env vars are not present
    endpoint = None  # endpoint is set to None to make it a global variable

    makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
    log_file = datetime.now().strftime('logs' + path.sep + 'auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    base_file = PurePath(__file__)  # PurePath(__file__).stem strips the extension/suffixes of the file

    fileLogger, consoleLogger, rootLogger = logging_wrapper()

    if (not (gmail_user := environ.get('gmail_user')) or not
            (gmail_pass := environ.get('gmail_pass')) or not
            (recipient := environ.get('recipient'))):
        notify = False
        rootLogger.warning(
            f"Consider storing the following env vars to receive an email notification when PersonalCloud is accessed"
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
            "gmail_user='xxx@gmail.com'\n"
            "gmail_pass='*************'\n"
            "recipient='yyy@zzz.com'\n\n"
            f"{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
        )

    auth_success, login_failed, session_expiry = [Path(f'html/{file}').read_text() for file in listdir('html')]

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
