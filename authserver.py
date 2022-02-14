import logging
import os
from base64 import b64decode, b64encode
from binascii import Error
from datetime import datetime
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from importlib import reload
from inspect import currentframe
from pathlib import Path, PurePath
from socket import AF_INET, SOCK_DGRAM, gethostbyname, socket
from ssl import wrap_socket
from time import time
from urllib.request import urlopen

from gmailconnector.send_email import SendEmail
from yaml import FullLoader, dump, load

from helper_functions.cert import generate_cert
from helper_functions.ngrok import checker
from helper_functions.ngrok import host as optional_host
from helper_functions.ngrok import port
from helper_functions.ngrok_fetcher import get_ngrok


# noinspection PyPep8Naming
class Authenticator(SimpleHTTPRequestHandler):
    """Main class to present webpages and authentication.

    >>> Authenticator

    Notes:
        - `Authenticator` uses encrypted server side header authentication.
        - Browser's default pop up will be shown prompting the user to enter the username and password.
        - Enter the Username and Password that was set in `environment variables <https://git.io/JCfzq>`__
        - The username and password are set as encoded auth headers, which are matched against the encoded env vars.
        - Upon successful authentication, a welcome page loads. Click on proceed to access the PersonalCloud.

    See Also:
        - To perform authentication, a `do_AUTH()` is implemented sending 401 and WWW-Authenticate header in response.
        - To handle `POST` requests, a `do_POST()` has been implemented, which reads `content-length` header.
        - Headers are read using `rfile.read` from the start of the optional input data.
        - Data is sent to server using, `wfile.write` which contains the output stream to write response to the client.
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
            if os.path.isdir(target_path) and 'index.html' in os.listdir(target_path):
                old_name = target_path + 'index.html'
                new_name = target_path + 'index_TEMP.html'
                consoleLogger.critical(f'Renaming {old_name} to {new_name}')
                os.rename(old_name, new_name)
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
        global endpoint, authenticated, first_run
        now = datetime.now()
        client_file = 'client_info.yaml'
        length = int(self.headers.get('content-length'))
        peanut = self.rfile.read(length)
        butter = peanut.decode(encoding='UTF-8').split('&')[0]
        if butter == 'LOGOUT':
            rootLogger.critical("Logout has been requested. Resetting auth headers to False.")
            first_run = True  # to reset and give a fresh start
            authenticated = False  # to show Login Success screen the next time
            return
        client_info = load(butter, Loader=FullLoader)
        if client_info.get('ip') == load(urlopen('https://ipapi.co/json/'), Loader=FullLoader).get('ip'):
            consoleLogger.info(f"Internal connection request received. Response: {client_info.get('_html_ref')}")
            return
        rootLogger.fatal(str(client_info).strip("{}").replace("'", ""))

        if os.path.isfile(client_file):
            with open(client_file, 'r') as client:
                exist = load(''.join([nut for nut in client.readlines() if not nut.startswith('#')]), Loader=FullLoader)

            # avoids duplicate notification for repeated trials in less than 5 minutes
            if int(now.timestamp()) - int(os.stat(client_file).st_mtime) < 300 and \
                    client_info.get('_html_ref') == exist.get('_html_ref') and \
                    client_info.get('ip') == exist.get('ip'):
                rootLogger.critical(f"{exist.get('ip')} performed {exist.get('_html_ref')} once again within 5 minutes")
                return

        current_time = f"Server Datetime: {now.strftime('%B %d, %Y %I:%M %p')}"
        hashes = ''.join(['#' for _ in range(74)])
        with open(client_file, 'w') as client:
            client.write(f"{hashes}\n#\t\t\t\t{current_time}\n{hashes}\n")
            dump(client_info, client, indent=4)

        if not (status := client_info.get('_html_ref')):
            status = 'An undefined login attempt'

        if not notify or status not in ['LOGIN SUCCESS', 'An undefined login attempt']:
            return

        if global_endpoint := get_ngrok():
            endpoint = global_endpoint
        else:
            endpoint = endpoint or f"http://{':'.join(map(str, self.connection.getsockname()))}"

        with open(client_file, 'r') as client:
            attachment_info = client.read()

        email_body = f"A connection with status `{status}` has been made to your personal cloud serving at " \
                     f"{endpoint}\n\nDetails of the client are below. If this was you, you may disregard this email. " \
                     f"Otherwise stop the server immediately and rotate your credentials before restarting." \
                     f"\n\n\n{attachment_info}\n\n"

        if host_dir == home_dir:
            email_body += f"\n\n\nLogs: {endpoint}/{(str(base_file).strip(base_file.name) + log_file).strip(host_dir)}"

        response = SendEmail(gmail_user=gmail_user, gmail_pass=gmail_pass, recipient=recipient,
                             subject=f"WARNING: {status} was detected. {current_time}", attachment=client_file,
                             body=email_body).send_email()
        if response.ok:
            rootLogger.info('Email has been sent successfully.')
        else:
            rootLogger.error(response.body)

    def disable_cache(self) -> None:
        """Headers to force no-cache and site-data to expire."""
        if 'Cache-Control' in self.headers.keys():
            self.headers.replace_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        else:
            self.headers.add_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        self.headers.add_header(_name='Pragma', _value='no-cache')
        self.headers.add_header(_name='Expires', _value='0')
        self.headers.add_header(_name='Clear-Site-Data', _value='"cache", "cookies", "storage", "executionContexts"')


def reset_auth() -> bool:
    """Tells if the authentication header has to be reset and cache to be cleared.

    See Also:
        Note that if an authentication is done at the end of 15 minutes, there will be a re-auth prompted.

    Returns:
        bool:
        True if it is the first login attempt, or it has been more than 15 minutes since the first/previous expiry.
    """
    global start_time, first_run
    if first_run:
        first_run = False
        return True
    elif time() - start_time > 900:
        start_time = time()
        return True


def server_function(ssl: bool) -> None:
    """Uses local certificate from ~.ssh to serve the page as https if flag is set to True.

    Args:
        ssl: Whether to wrap the socket with the certificate.
    """
    global endpoint
    rootLogger.info('Initiating file server.')
    handler_class = partial(
        Authenticator,
        username=username,
        password=password,
        directory=host_dir
    )
    server = HTTPServer(server_address=(host, port), RequestHandlerClass=handler_class)

    if ssl:
        server.socket = wrap_socket(sock=server.socket, server_side=True, certfile=cert_file, keyfile=key_file)
        endpoint = f"https://{':'.join(map(str, server.server_address))}"
    else:
        endpoint = f"http://{':'.join(map(str, server.server_address))}"
    print(f"{line_number()} - Serving at: {endpoint}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        [(os.rename(new_name, old_name), consoleLogger.critical(f'Reverted {new_name} to {old_name}'))
         for each in renamed for old_name, new_name in each.items() if renamed]
        rootLogger.info('Terminating file server.')
        server.server_close()
        server.shutdown()
        print(f"{line_number()} - File server has been terminated.")


def line_number() -> int:
    """Uses the inspect module to fetch the line number from current frame.

    Returns:
        int:
        Line number of where this function is called.
    """
    return currentframe().f_back.f_lineno


def file_gatherer() -> list:
    """Uses `pathlib.Path(file).read_text()` to read the files.

    Notes:
        Actual way of doing this is to open and read the file individually. But I'm a fan of list comprehensions.

        `auth_success, login_failed, session_expiry = [open(f'html/{file}').read() for file in os.listdir('html')]`

        But opening a file in list comprehension leaves the file open through out the code execution.
        This can be verified using `psutil.Process().open_files()`

    Returns:
        list:
        Returns the data in each file within the html directory.
    """
    return [Path(f'html/{file}').read_text() for file in os.listdir('html')]


def logging_wrapper() -> tuple:
    """Wraps logging module to create multiple handlers for different purposes.

    See Also:
        - fileLogger: Writes the log information only to the log file.
        - consoleLogger: Writes the log information only in stdout.
        - rootLogger: Logs the entry in both stdout and log file.

    Returns:
        tuple:
        A tuple of classes logging.Logger for file, console and root logging.
    """
    reload(logging)  # since the gmail-connector module uses logging, it is better to reload logging module before start
    os.makedirs('logs') if 'logs' not in os.listdir(os.getcwd()) else None  # create logs directory if not found
    log_formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
        datefmt='%b-%d-%Y %H:%M:%S'
    )

    file_logger = logging.getLogger('FILE')
    console_logger = logging.getLogger('CONSOLE')
    root_logger = logging.getLogger(base_file.stem)

    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(fmt=log_formatter)
    file_logger.setLevel(level=logging.INFO)
    file_logger.addHandler(hdlr=file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt=log_formatter)
    console_logger.setLevel(level=logging.INFO)
    console_logger.addHandler(hdlr=console_handler)

    root_logger.addHandler(hdlr=file_handler)
    root_logger.addHandler(hdlr=console_handler)
    return file_logger, console_logger, root_logger


if __name__ == "__main__":
    if not (username := os.environ.get('username', os.environ.get('USER'))) or \
            not (password := os.environ.get('password')):
        exit('Add username and password in local ENV VARS to proceed.')

    start_time = time()  # set to the current time to reset the auth headers when timeout is reached
    first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
    authenticated = False  # set to False for the appropriate message to be written in the HTML file
    renamed = []  # set to empty list to append dictionaries with re-namings done for index.html
    notify = True  # notify is set to true by default unless the env vars are not present
    endpoint = None  # endpoint is set to None to make it a global variable

    os.makedirs('logs') if 'logs' not in os.listdir(os.getcwd()) else None  # create logs directory if not found
    log_file = datetime.now().strftime('logs' + os.path.sep + 'auth_server_%H:%M:%S_%d-%m-%Y.log')  # set log file name
    base_file = PurePath(__file__)  # PurePath(__file__).stem strips the extension/suffixes of the file

    fileLogger, consoleLogger, rootLogger = logging_wrapper()

    if (not (gmail_user := os.environ.get('gmail_user')) or not
            (gmail_pass := os.environ.get('gmail_pass')) or not
            (recipient := os.environ.get('recipient'))):
        notify = False
        rootLogger.warning(
            f"Consider storing the following env vars to receive an email notification when PersonalCloud is accessed"
            f"\n{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
            "gmail_user='xxx@gmail.com'\n"
            "gmail_pass='*************'\n"
            "recipient='yyy@zzz.com'\n\n"
            f"{''.join(['*' for _ in range(120)])}\n"  # PEP 8 default: 120 columns
        )

    auth_success, login_failed, session_expiry = [Path(f'html/{file}').read_text() for file in os.listdir('html')]

    home_dir = os.path.expanduser('~')
    if not (host_dir := os.environ.get('host_path')) or not os.path.isdir(host_dir):
        host_dir = home_dir

    ssh_dir = home_dir + os.path.sep + os.path.join('.ssh')
    cert_file = os.path.expanduser(ssh_dir) + os.path.sep + "cert.pem"
    key_file = os.path.expanduser(ssh_dir) + os.path.sep + "key.pem"

    if checker():
        host = optional_host
        server_function(ssl=False)  # ngrok uses its own SSL cert for https connection
    else:
        ip_socket = socket(AF_INET, SOCK_DGRAM)
        ip_socket.connect(("8.8.8.8", 80))
        if not (host := ip_socket.getsockname()[0]):
            host = gethostbyname('localhost')
        ip_socket.close()
        if os.path.isfile(cert_file) and os.path.isfile(key_file):
            server_function(ssl=True)
        elif generate_cert(common_name='*.ngrok.com', cert_file=cert_file, key_file=key_file):
            server_function(ssl=True)
        else:
            server_function(ssl=False)
