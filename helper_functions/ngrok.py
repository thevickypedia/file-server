from logging import INFO, basicConfig, getLogger
from os import environ, listdir, remove, system
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, gethostbyname, socket
from subprocess import check_output

from pyngrok.exception import PyngrokError
from pyngrok.ngrok import connect, kill

basicConfig(format="%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - Line: %(lineno)d - %(message)s",
            level=INFO)
getLogger(name='pyngrok').propagate = False  # disable module level logging
logger = getLogger(Path(__file__).stem)


def writer(url) -> None:
    """Writes the received url into a file named `url`.

    Notes:
        - This is to support `Jarvis <https://github.com/thevickypedia/Jarvis>`__
        - Jarvis scans the url file to fetch the public_url and sends it to the end user.

    Args:
        url: Public URL generated by Ngrok.

    """
    if 'url' in listdir():
        remove('url')
    with open('url', 'w') as url_file:
        url_file.write(url)


def restart() -> None:
    """Restarts `ngrok.py <https://git.io/JchBu>`__.

    See Also:
        - Restart kills any active sessions of ngrok.
        - Once done, it triggers `restart.py <https://git.io/JchB1>`__ which in turn starts ngrok after 5 seconds.
        - Note that only the `ngrok` processID will be terminated and not the terminal/session that is tunneling it.

    """
    pid_check = check_output("ps -ef | grep ngrok", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_.endswith('start --none --log=stdout'):
            logger.info(f'{id_.split()[1]} will be terminated to close the active session.')
            system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout
    system('python3 restart.py')
    exit(1)


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
    port = environ.get('port', 4443)
    host = gethostbyname('localhost')

    sock = socket(AF_INET, SOCK_STREAM)

    # # Uncomment bind to create a whole new connection to the port
    # server_address = (host, port)  # Bind a local socket to the port
    # sock.bind(server_address)  # Bind only accepts tuples

    sock.listen(1)

    public_url = None
    try:
        endpoint = connect(port, "http", options={"remote_addr": f"{host}:{port}"})  # Open a ngrok tunnel to the socket
        public_url = endpoint.public_url.replace('http', 'https')
        writer(public_url)
    except PyngrokError as err:
        logger.error(err)
        if 'is limited to 1 simultaneous ngrok client session' in str(err):
            restart()
        else:
            writer('Ngrok failed.')
            return

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
