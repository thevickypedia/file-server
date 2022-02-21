import functools
import os
import ssl
import warnings
from http.server import HTTPServer
from multiprocessing import Process
from socket import AF_INET, SOCK_DGRAM, socket
from typing import AnyStr, Union
from uuid import UUID

from . import cert, env, models, ngrok
from .responder import Response
from .server import Authenticator

logger = models.server_logger()


class FileWare:
    """Class to instantiate FileWare object, and run the file server in a thread.

    >>> FileWare

    """

    def __init__(self, port: Union[int, str] = None, username: AnyStr = None, password: AnyStr = None,
                 host_dir: AnyStr = None, ngrok_auth: Union[UUID, str] = None, gmail_user: str = None,
                 gmail_pass: str = None, recipient: str = None) -> None:
        """Initiates the ``FileWare``.

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
            - All these arguments can be loaded via env vars by placing the key-value pairs in a ``.env`` file.
            - The ``.env`` file should be stored in the current working directory.
        """
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

    @staticmethod
    def initiate_connection() -> Response:
        """Initiates fileserver connection after trying to trigger ngrok tunnel.

        See Also:
            - Checks for ``cert.pem`` and ``key.pem`` files in ~home/ssh path.
            - If not generates a self-signed certificate using ``OpenSSL``
            - If ngrok tunnel is running on the port already, initiates file server on localhost else uses local IP.
        """
        socket_connection, public_url = ngrok.connect()
        ssh_dir = env.home_dir + os.path.sep + os.path.join('.ssh')
        cert_file = os.path.expanduser(ssh_dir) + os.path.sep + "cert.pem"
        key_file = os.path.expanduser(ssh_dir) + os.path.sep + "key.pem"

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
        if socket_connection:
            logger.info(f"Hosted at public endpoint: {public_url}")
        return Response({
            'socket': socket_connection,
            'server': http_server,
            'url': public_url or endpoint
        })

    @staticmethod
    def serve(http_server: HTTPServer, socket_connection: socket = None) -> None:
        """Starts the file server session.

        Args:
            http_server: Takes the HTTPServer object as an argument.
            socket_connection: Socket connection in case ngrok tunneling is active.
        """
        process = None
        if socket_connection:
            process = Process(target=ngrok.tunnel, kwargs={'sock': socket_connection})
            process.start()

        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            if process:
                process.join(timeout=10)
            [(os.rename(new_name, old_name), logger.critical(f'Reverted {new_name} to {old_name}'))
             for each in env.renamed for old_name, new_name in each.items() if env.renamed]
            logger.info('Terminating file server.')
            http_server.server_close()
            http_server.shutdown()
            logger.info("File server has been terminated.")
