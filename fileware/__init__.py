import functools
import os
import ssl
import warnings
from http.server import HTTPServer
from multiprocessing import Process
from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, socket
from typing import AnyStr, Union

from . import cert, env, models, ngrok
from .responder import Response
from .server import Authenticator

logger = models.server_logger()


def is_port_in_use(port: int) -> bool:
    """Connect to a remote socket at address.

    Args:
        port: Takes the port number as an argument.

    Returns:
        bool:
        A boolean flag to indicate whether a port is open.
    """
    with socket(AF_INET, SOCK_STREAM) as sock:
        return sock.connect_ex(('localhost', port)) == 0


def override_env_vars(port: Union[int, str] = None, username: AnyStr = None, password: AnyStr = None,
                      host_dir: AnyStr = None, ngrok_auth: AnyStr = None, gmail_user: str = None,
                      gmail_pass: str = None, recipient: str = None) -> None:
    """Overrides the env vars (even the ones loaded from a `.env` file) by assigning them to global values.

    Args:
        port: Port number in which the file server is running.
        username: Username to access fileserver.
        password: Password to access fileserver.
        host_dir: Takes the path to serve as an argument. Can also be loaded via env vars.
        ngrok_auth: Ngrok auth token for tunneling.
        gmail_user: Username for email notification.
        gmail_pass: Password for email notification.
        recipient: Email address to receive notification.

    See Also:
        - All these arguments can be loaded via env vars instead or by placing them in a ``.env`` file.
        - This function is only to override the existing env vars.
    """
    overridden = [key for key, value in locals().items() if value]
    logger.warning(f'Overriding env vars: {overridden}')
    if port:
        env.port = port
    if gmail_user:
        env.gmail_user = gmail_user
    if gmail_pass:
        env.gmail_pass = gmail_pass
    if recipient:
        env.recipient = recipient
    if username:
        env.username = username
    if password:
        env.password = password
    if ngrok_auth:
        env.ngrok_auth = ngrok_auth
    if host_dir:
        if os.path.isdir(host_dir):
            env.host_dir = host_dir
        else:
            warnings.warn(f"The specified path: {host_dir} doesn't exist. Defaulting to {env.host_dir}")


def initiate_connection() -> Response:
    """Initiates fileserver connection after trying to trigger ngrok tunnel.

    See Also:
        - Checks for ``cert.pem`` and ``key.pem`` files in ``~home/ssh`` directory.
        - If not, generates a self-signed certificate using ``OpenSSL``
        - If ngrok tunnel is running on the port already, initiates file server on localhost else uses local IP.
    """
    if is_port_in_use(port=env.port):
        logger.critical(f'Port number: {env.port} is currently being used.')
        socket_connection, public_url = None, None
    else:
        socket_connection, public_url = ngrok.connect()

    cert_file = os.path.join(env.home_dir, ".ssh", "cert.pem")
    key_file = os.path.join(env.home_dir, ".ssh", "key.pem")

    if not socket_connection:
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
    http_server = HTTPServer(server_address=(env.host, env.port), RequestHandlerClass=handler_class)

    if not socket_connection and all([os.path.isfile(cert_file), os.path.isfile(key_file)]):
        http_server.socket = ssl.wrap_socket(sock=http_server.socket, server_side=True,
                                             certfile=cert_file, keyfile=key_file)
        endpoint = f"https://{':'.join(map(str, http_server.server_address))}"
    else:
        endpoint = f"http://{':'.join(map(str, http_server.server_address))}"

    logger.info(f"Serving at: {endpoint}")
    process = None
    if socket_connection:
        logger.info(f"Hosted at public endpoint: {public_url}")
        process = Process(target=ngrok.tunnel, kwargs={'sock': socket_connection})

    return Response({
        'url': public_url or endpoint,
        'server': http_server,
        'process': process
    })


def serve(http_server: HTTPServer, process: Process = None) -> None:
    """Starts the file server session.

    Args:
        http_server: Takes the HTTPServer object as an argument.
        process: Process used to spin up ngrok tunnel.
    """
    if process:
        process.start()
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        shutdown(http_server=http_server, process=process)


def shutdown(http_server: HTTPServer, process: Process = None) -> None:
    """Terminates the web server and the ngrok process if available.

    Args:
        http_server: Web server.
        process: Ngrok process to end.
    """
    env.STOPPER = True
    if process:
        process.join(timeout=2e-1)
    [(os.rename(new_name, old_name), logger.critical(f'Reverted {new_name} to {old_name}'))
     for each in env.renamed for old_name, new_name in each.items() if env.renamed]
    logger.info('Terminating file server.')
    http_server.server_close()
    http_server.shutdown()
    logger.info("File server has been terminated.")
