import base64
import binascii
import os
from http.server import SimpleHTTPRequestHandler
from pathlib import PurePath
from time import time

import yaml

from . import models, settings

logger = models.server_logger()

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
        """Suppresses logs from ``http.server`` by holding the args.

        Overwrites the base method: `BaseHTTPRequestHandler.log_message()`

        Args:
            format_: String operator %s
            *args: Logs from SimpleHTTPRequestHandler displaying request method type and HTTP status code.
        """
        if not hasattr(self, 'path'):
            return
        if len(args) == 3:  # We don't have to care about NOT FOUND items because they are mostly hidden/protected.
            method, status_code, ignore = args  # ignore always returns `-`
            method = str(method).split('/')[0].strip()
            if int(str(status_code).strip()) == 200:
                logger.info('Received %d while accessing a %s method to reach %s',
                            status_code, method, self.path)
            else:
                logger.error('Received %d while accessing a %s method to reach %s',
                             status_code, method, self.path)

    def do_HEAD(self) -> None:
        """Sends 200 response and sends headers when authentication is successful."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    # noinspection PyProtectedMember
    def do_GET(self) -> None:
        """Serve a front end with user authentication."""
        if _reset_auth() and 'Authorization' in self.headers.keys():
            logger.warning('Authorized via stored cookies. However session expired, so headers have been reset.')
            self.headers.replace_header('Authorization', None)
            self.disable_cache()

        if not (auth_header := self.headers.get("Authorization")):
            self.do_AUTH()
            if not settings._authenticated:
                self.wfile.write(login_failed.encode(encoding='UTF-8'))
            else:
                self.wfile.write(session_expiry.encode(encoding='UTF-8'))
        elif auth_header == "Basic " + self._auth:
            target_path = os.path.join(models.env.host_dir, self.path)
            if os.path.isdir(target_path) and 'index.html' in os.listdir(target_path):
                old_name = target_path + 'index.html'
                new_name = target_path + 'index_TEMP.html'
                logger.critical(f'Renaming {old_name} to {new_name}')
                os.rename(old_name, new_name)
                settings._renamed.append({old_name: new_name})
            if not settings._authenticated:
                self.do_HEAD()
                self.wfile.write(auth_success.encode(encoding='UTF-8'))
                settings._authenticated = True
                return
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except BrokenPipeError:
                pass
        else:
            self.do_AUTH()
            auth = auth_header.strip('Basic ')
            try:
                auth = base64.b64decode(auth).decode().split(':')
                logger.error('Authentication Blocked: Username: %s\tPassword: %s', auth[0], auth[1])
            except binascii.Error:
                logger.error('Authentication Blocked: Encoded: %s', auth)

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
        if butter == 'LOGOUT':
            logger.critical("Logout has been requested. Resetting auth headers to False.")
            settings._first_run = True  # to reset and give a fresh start
            settings._authenticated = False  # to show Login Success screen the next time
            return
        client_info = yaml.load(butter, Loader=yaml.FullLoader)
        filename = f"{client_info.get('ip')}.yaml"
        if os.path.isfile(filename):
            return
        with open(filename, "w") as f:
            yaml.dump(data=client_info, stream=f)

    def disable_cache(self) -> None:
        """Headers to force no-cache and site-data to expire."""
        if 'Cache-Control' in self.headers.keys():
            self.headers.replace_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        else:
            self.headers.add_header(_name='Cache-Control', _value='no-cache, no-store, must-revalidate')
        self.headers.add_header(_name='Pragma', _value='no-cache')
        self.headers.add_header(_name='Expires', _value='0')
        self.headers.add_header(_name='Clear-Site-Data', _value='"cache", "cookies", "storage", "executionContexts"')


# noinspection PyProtectedMember
def _reset_auth() -> bool:
    """Tells if the authentication header has to be reset and cache to be cleared.

    See Also:
        Note that if an authentication is done at the end of 15 minutes, there will be a re-auth prompted.

    Returns:
        bool:
        True if it is the first login attempt, or it has been more than 15 minutes since the first/previous expiry.
    """
    if settings._first_run:
        settings._first_run = False
        return True
    elif time() - settings._start_time > 900:
        settings._start_time = time()
        return True
