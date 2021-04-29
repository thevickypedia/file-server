from logging import getLogger, basicConfig, INFO
from os import environ
from pathlib import Path
from socket import socket, AF_INET, SOCK_STREAM, gethostbyname

from pyngrok.ngrok import connect

basicConfig(level=INFO)
getLogger(name='pyngrok').propagate = False  # disable module level logging
logger = getLogger(Path(__file__).stem)
port = environ.get('PORT')
host = gethostbyname('localhost')

sock = socket(AF_INET, SOCK_STREAM)  # Create a TCP socket

# # Uncomment bind to create a whole new connection to the port
# server_address = (host, port)  # Bind a local socket to the port
# sock.bind(server_address)  # Bind only accepts tuples

sock.listen(1)

public_url = connect(port, "tcp", options={"remote_addr": f"{host}:{port}"})  # Open a ngrok tunnel to the socket
url = str(public_url).split()[1].replace('"', '').replace('tcp://', 'http://')

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
