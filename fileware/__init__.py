import functools
import os
import ssl
from http.server import HTTPServer
from multiprocessing import Process
from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, socket

from . import cert, env, models, ngrok, settings
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


# noinspection PyProtectedMember
def initiate_connection(localhost: bool = True, secure: bool = True) -> Response:
    """Initiates file-server connection after trying to trigger ngrok tunnel.

    Args:
        localhost: Takes a boolean value whether to host the server on 127.0.0.1 or local IP address.
        secure: Takes a boolean flag whether to bind the ssl cert.

    See Also:
        - Checks for ``cert.pem`` and ``key.pem`` files in ``~home/ssh`` directory.
        - If not, generates a self-signed certificate using ``OpenSSL``
        - If ngrok tunnel is running on the port already, initiates file server on localhost else uses local IP.
    """
    if not env.password:
        raise ValueError("password is mandatory")
    socket_connection, public_url = None, None
    if is_port_in_use(port=env.port):
        logger.critical(f'Port number: {env.port} is currently being used.')
    elif localhost:
        socket_connection, public_url = ngrok.connect()

    cert_file = os.path.join(settings._home_dir, ".ssh", "cert.pem")
    key_file = os.path.join(settings._home_dir, ".ssh", "key.pem")

    if not socket_connection and not localhost:
        ip_socket = socket(AF_INET, SOCK_DGRAM)
        ip_socket.connect(("8.8.8.8", 80))
        settings._host = ip_socket.getsockname()[0]
        if not all([os.path.isfile(cert_file), os.path.isfile(key_file)]):
            cert.generate_cert(common_name='*.ngrok.com', cert_file=cert_file, key_file=key_file)

    logger.info('Initiating file server.')
    handler_class = functools.partial(
        Authenticator,
        username=env.username,
        password=env.password,
        directory=env.host_dir
    )
    http_server = HTTPServer(server_address=(settings._host, env.port), RequestHandlerClass=handler_class)

    if not socket_connection and all([os.path.isfile(cert_file), os.path.isfile(key_file)]) and secure:
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


# noinspection PyProtectedMember
def shutdown(http_server: HTTPServer, process: Process = None) -> None:
    """Terminates the web server and the ngrok process if available.

    Args:
        http_server: Web server.
        process: Ngrok process to end.
    """
    if process:
        logger.info("Stopping ngrok tunnel.")
        if process.is_alive():
            process.join(timeout=2e-1)
        if process.is_alive():
            process.terminate()
        if process.is_alive():
            process.kill()
    [(os.rename(new_name, old_name), logger.critical(f'Reverted {new_name} to {old_name}'))
     for each in settings._renamed for old_name, new_name in each.items() if settings._renamed]
    logger.info('Terminating file server.')
    http_server.server_close()
    http_server.shutdown()
    logger.info("File server has been terminated.")
