from logging import INFO, basicConfig, getLogger
from os import environ
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, gethostbyname, socket

from pyngrok.exception import PyngrokError
from pyngrok.ngrok import connect, kill


def tunnel() -> None:
    """Creates an HTTP socket and uses `pyngrok` module to bind the socket.

    Once the socket is bound, the listener is activated and runs in a forever loop accepting connections.

    See Also:
        Run the following code to setup.

        `from os import environ`

        `from pyngrok import conf`

        `conf.get_default().config_path = "/opt/ngrok/ngrok.yml"`

        `ngrok.set_auth_token(environ.get("NGROK_AUTH_TOKEN"))`

    """
    basicConfig(format="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
                level=INFO)
    getLogger(name='pyngrok').propagate = False  # disable module level logging
    logger = getLogger(Path(__file__).stem)
    port = environ.get('PORT', 4443)
    host = gethostbyname('localhost')

    sock = socket(AF_INET, SOCK_STREAM)

    # # Uncomment bind to create a whole new connection to the port
    # server_address = (host, port)  # Bind a local socket to the port
    # sock.bind(server_address)  # Bind only accepts tuples

    sock.listen(1)

    public_url = None
    try:
        public_url = connect(port, "http",
                             options={"remote_addr": f"{host}:{port}"})  # Open a ngrok tunnel to the socket
    except PyngrokError as err:
        exit(err)

    logger.info(f'Hosting to the public URL: {public_url}')

    connection = None
    while True:
        try:
            # Wait for a connection
            logger.info("Waiting for a connection")
            connection, client_address = sock.accept()
            logger.info(f"Connection established from {client_address}")
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            if connection:
                connection.close()
            break

    kill(pyngrok_config=None)  # uses default config when None is passed
    sock.close()


if __name__ == '__main__':
    tunnel()
