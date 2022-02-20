import base64
import binascii
import functools
import logging.config
import os
import ssl
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from multiprocessing import Process
from pathlib import Path, PurePath
from socket import AF_INET, SOCK_DGRAM, socket
from time import time
from urllib.request import urlopen

import yaml
from gmailconnector.send_email import SendEmail

from . import cert, env, models, ngrok

if not os.path.isfile(models.LogConfig.SERVER_LOG_FILE):
    Path(models.LogConfig.SERVER_LOG_FILE).touch()

logging.config.dictConfig(config=models.LogConfig.LOGGING_CONFIG)
logger = logging.getLogger('server')

HTML_PATH = f"{PurePath(__file__).parent}{os.path.sep}html{os.path.sep}"

with open(f'{HTML_PATH}auth_server.html') as file:
    auth_success = file.read()

with open(f'{HTML_PATH}no_auth.html') as file:
    login_failed = file.read()

with open(f'{HTML_PATH}session.html') as file:
    session_expiry = file.read()


# noinspection PyPep8Naming
class Authenticator(SimpleHTTPRequestHandler):
    """Main class to present webpages and authentication.

    >>> Authenticator

    Notes:
        - `Authenticator` uses encrypted server side header authentication.
        - Browser's default pop up will be shown prompting the user to enter the username and password.
        - Enter the Username and Password that was set in `environment variables <https://git.io/JCfzq>`__
        - The username and password are set as encoded auth headers, which are matched against the encoded env vars.
        - Upon successful authentication, a welcome page loads. Click on proceed to access the FileServer.

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
        self._auth = base64.b64encode(f"{kwargs.pop('username')}:{kwargs.pop('password')}".encode()).decode()
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
                logger.info(f'Received {status_code} while accessing a {method} method to reach {self.path}')
            else:
                logger.error(f'Received {status_code} while accessing a {method} method to reach {self.path}')

    def do_HEAD(self) -> None:
        """Sends 200 response and sends headers when authentication is successful."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self) -> None:
        """Serve a front end with user authentication."""
        if _reset_auth() and 'Authorization' in self.headers.keys():
            logger.warning('Authorized via stored cookies. However session expired, so headers have been reset.')
            self.headers.replace_header('Authorization', None)
            self.disable_cache()

        if not (auth_header := self.headers.get("Authorization")):
            self.do_AUTH()
            if not env.authenticated:
                self.wfile.write(login_failed.encode(encoding='UTF-8'))
            else:
                self.wfile.write(session_expiry.encode(encoding='UTF-8'))
        elif auth_header == "Basic " + self._auth:
            target_path = env.host_dir + self.path
            if os.path.isdir(target_path) and 'index.html' in os.listdir(target_path):
                old_name = target_path + 'index.html'
                new_name = target_path + 'index_TEMP.html'
                logger.critical(f'Renaming {old_name} to {new_name}')
                os.rename(old_name, new_name)
                env.renamed.append({old_name: new_name})
            if not env.authenticated:
                self.do_HEAD()
                self.wfile.write(auth_success.encode(encoding='UTF-8'))
                env.authenticated = True
                return
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except BrokenPipeError:
                logger.error(f'Received BrokenPipeError while reaching {self.path}')
        else:
            self.do_AUTH()
            auth = auth_header.strip('Basic ')
            try:
                auth = base64.b64decode(auth).decode().split(':')
                logger.error(f'Authentication Blocked: Username: {auth[0]}\tPassword: {auth[1]}')
            except binascii.Error:
                logger.error(f'Authentication Blocked: Encoded: {auth}')

    def do_AUTH(self) -> None:
        """Sends headers to authenticate the requester."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Test"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self) -> None:
        """Handles POST request and writes the received data into a yaml file."""
        now = datetime.now()
        client_file = 'client_info.yaml'
        length = int(self.headers.get('content-length'))
        peanut = self.rfile.read(length)
        butter = peanut.decode(encoding='UTF-8').split('&')[0]
        if butter == 'LOGOUT':
            logger.critical("Logout has been requested. Resetting auth headers to False.")
            env.first_run = True  # to reset and give a fresh start
            env.authenticated = False  # to show Login Success screen the next time
            return
        client_info = yaml.load(butter, Loader=yaml.FullLoader)
        if client_info.get('ip') == yaml.load(urlopen('https://ipapi.co/json/'), Loader=yaml.FullLoader).get('ip'):
            logger.info(f"Internal connection request received. Response: {client_info.get('_html_ref')}")
            return
        logger.fatal(str(client_info).strip("{}").replace("'", ""))

        if os.path.isfile(client_file):
            with open(client_file, 'r') as client:
                exist = yaml.load(''.join([nut for nut in client.readlines() if not nut.startswith('#')]),
                                  Loader=yaml.FullLoader)

            # avoids duplicate notification for repeated trials in less than 5 minutes
            if int(now.timestamp()) - int(os.stat(client_file).st_mtime) < 300 and \
                    client_info.get('_html_ref') == exist.get('_html_ref') and \
                    client_info.get('ip') == exist.get('ip'):
                logger.critical(f"{exist.get('ip')} performed {exist.get('_html_ref')} once again within 5 minutes")
                return

        current_time = f"Server Datetime: {now.strftime('%B %d, %Y %I:%M %p')}"
        hashes = ''.join(['#' for _ in range(74)])
        with open(client_file, 'w') as client:
            client.write(f"{hashes}\n#\t\t\t\t{current_time}\n{hashes}\n")
            yaml.dump(client_info, client, indent=4)

        if not (status := client_info.get('_html_ref')):
            status = 'An undefined login attempt'

        if not all([env.gmail_user, env.gmail_pass, env.recipient]) or status not in ['LOGIN SUCCESS',
                                                                                      'An undefined login attempt']:
            return

        if not (endpoint := ngrok.get_ngrok()):
            endpoint = env.endpoint or f"http://{':'.join(map(str, self.connection.getsockname()))}"

        with open(client_file, 'r') as client:
            attachment_info = client.read()

        body = f"A connection with status `{status}` has been made to your file server hosted at " \
               f"{endpoint}\n\nDetails of the client are below. If this was you, you may disregard this email. " \
               f"Otherwise stop the server immediately and rotate your credentials before restarting." \
               f"\n\n\n{attachment_info}\n\n"

        if env.host_dir == env.home_dir:
            base_path = PurePath(__file__)
            body += f"\n\n\nLogs: {endpoint}/" \
                    f"{(str(base_path).strip(base_path.name) + models.LogConfig.SERVER_LOG_FILE).strip(env.host_dir)}"

        response = SendEmail(gmail_user=env.gmail_user, gmail_pass=env.gmail_pass, recipient=env.recipient,
                             subject=f"WARNING: {status} was detected. {current_time}", attachment=client_file,
                             body=body).send_email()
        if response.ok:
            logger.info('Email has been sent successfully.')
        else:
            logger.error(response.body)

    def disable_cache(self) -> None:
        """Headers to force no-cache and site-data to expire."""
        if 'Cache-Control' in self.headers.keys():
            self.headers.replace_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        else:
            self.headers.add_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        self.headers.add_header(_name='Pragma', _value='no-cache')
        self.headers.add_header(_name='Expires', _value='0')
        self.headers.add_header(_name='Clear-Site-Data', _value='"cache", "cookies", "storage", "executionContexts"')


def _reset_auth() -> bool:
    """Tells if the authentication header has to be reset and cache to be cleared.

    See Also:
        Note that if an authentication is done at the end of 15 minutes, there will be a re-auth prompted.

    Returns:
        bool:
        True if it is the first login attempt, or it has been more than 15 minutes since the first/previous expiry.
    """
    if env.first_run:
        env.first_run = False
        return True
    elif time() - env.start_time > 900:
        env.start_time = time()
        return True


def initiate_connection() -> None:
    """Initiates fileserver connection after trying to trigger ngrok tunnel.

    See Also:
        - Checks for ``cert.pem`` and ``key.pem`` files in ~home/ssh path.
        - If not generates a self-signed certificate using ``OpenSSL``
        - If ngrok tunnel is running on the port already, initiates file server on localhost else uses local IP.
    """
    socket_, public_url = ngrok.connect()
    if socket_ and public_url:
        Process(target=ngrok.tunnel, kwargs={'sock': socket_}).start()

    with open('url', 'w') as url_file:
        url_file.write(str(public_url))

    ssh_dir = env.home_dir + os.path.sep + os.path.join('.ssh')
    cert_file = os.path.expanduser(ssh_dir) + os.path.sep + "cert.pem"
    key_file = os.path.expanduser(ssh_dir) + os.path.sep + "key.pem"

    if not socket_:
        ip_socket = socket(AF_INET, SOCK_DGRAM)
        ip_socket.connect(("8.8.8.8", 80))
        env.host = ip_socket.getsockname()[0]
        if not all([os.path.isfile(cert_file), os.path.isfile(key_file)]):
            cert.generate_cert(common_name='*.ngrok.com', cert_file=cert_file, key_file=key_file)

    logger.info('Initiating file server.')
    handler_class = functools.partial(
        Authenticator,
        username=env.username,
        password=env.password,
        directory=env.host_dir
    )
    server = HTTPServer(server_address=(env.host, env.port), RequestHandlerClass=handler_class)

    if not socket_ and all([os.path.isfile(cert_file), os.path.isfile(key_file)]):
        server.socket = ssl.wrap_socket(sock=server.socket, server_side=True,
                                        certfile=cert_file, keyfile=key_file)
        endpoint = f"https://{':'.join(map(str, server.server_address))}"
    else:
        endpoint = f"http://{':'.join(map(str, server.server_address))}"

    logger.info(f"Serving at: {endpoint}")

    if public_url:
        logger.info(f"Hosted at public endpoint: {public_url}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        [(os.rename(new_name, old_name), logger.critical(f'Reverted {new_name} to {old_name}'))
         for each in env.renamed for old_name, new_name in each.items() if env.renamed]
        logger.info('Terminating file server.')
        server.server_close()
        server.shutdown()
        logger.info("File server has been terminated.")
        if os.path.isfile('url'):
            os.remove('url')
