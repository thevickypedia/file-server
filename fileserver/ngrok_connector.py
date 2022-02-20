import logging.config
import os
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket

import requests
import yaml
from pyngrok import conf, ngrok
from pyngrok.exception import PyngrokError
from requests.exceptions import ConnectionError, InvalidURL

from fileserver import env
from fileserver.models import LogConfig

os.makedirs('logs') if not os.path.isdir('logs') else None

if not os.path.isfile(LogConfig.TUNNEL_LOG_FILE):
    Path(LogConfig.TUNNEL_LOG_FILE).touch()

logging.config.dictConfig(config=LogConfig.LOGGING_CONFIG)
logger = logging.getLogger('tunnel')


def get_ngrok() -> str or None:
    """Identifies if an existing ngrok tunnel by sending a `GET` request to api/tunnels to get the `ngrok` public url.

    See Also:
        Checks for output from get_port function. If nothing, then `ngrok` isn't running.
        However, as a sanity check, the script uses port number stored in env var to make a `GET` request.

    Returns:
        str or None:
        - On success, returns the `ngrok` public URL.
        - On failure, returns None to exit function.
    """
    try:
        response = requests.get(f'http://{env.host}:4040/api/tunnels')
    except InvalidURL:
        return
    except ConnectionError:
        return

    serving_at = yaml.load(response.content.decode(), Loader=yaml.FullLoader)['tunnels']
    return serving_at[0].get('public_url')


def connect(new_connection: bool = False):
    """Creates an HTTP socket and uses `pyngrok` module to bind the socket.

    Args:
        new_connection: Takes a boolean flag whether to spin up a new connection.

    Once the socket is bound, the listener is activated and runs in a forever loop accepting connections.

    See Also:
        Run the following code to setup.

        .. code-block:: python
            :emphasize-lines: 4,7,10

            from pyngrok.conf import PyngrokConfig, get_default
            from pyngrok.ngrok import set_auth_token

            # Sets auth token only during run time without modifying global config.
            PyngrokConfig.auth_token = '<NGROK_AUTH_TOKEN>'

            # Uses auth token from the specified file without modifying global config.
            get_default().config_path = "/path/to/config.yml"

            # Changes auth token at $HOME/.ngrok2/ngrok.yml
            set_auth_token('<NGROK_AUTH_TOKEN>')

    Returns:
        tuple:
        A tuple of the connected socket and the public URL.
    """
    sock = socket(AF_INET, SOCK_STREAM)

    if new_connection:
        # Uncomment bind to create a whole new connection to the port
        server_address = (env.host, env.port)  # Bind a local socket to the port
        sock.bind(server_address)  # Bind only accepts tuples

    sock.listen(1)

    if env.ngrok_auth:
        ngrok.set_auth_token(env.ngrok_auth)
    elif os.path.isfile('ngrok.yml'):
        conf.get_default().config_path = 'ngrok.yml'
    else:
        return None, 'Tunneling is unavailable since ngrok config file is missing.'

    try:
        endpoint = ngrok.connect(env.port, "http", options={"remote_addr": f"{env.host}:{env.port}"})
        public_url = endpoint.public_url.replace('http', 'https')
    except PyngrokError as err:
        logger.error(err)
        return None, err

    return sock, public_url


def tunnel(sock: socket) -> None:
    """Initiates tunneling in a never ending loop.

    Args:
        sock: Takes the connected socket as an argument.
    """
    connection = None
    while True:
        try:
            logger.info("Waiting for a connection")
            connection, client_address = sock.accept()
            logger.info(f"Connection established from {client_address}")
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            if connection:
                connection.close()
            break

    ngrok.kill(pyngrok_config=None)  # uses default config when None is passed
    sock.close()


if __name__ == '__main__':
    print(get_ngrok())
