from socket import socket, AF_INET, SOCK_STREAM

from pyngrok.ngrok import connect

port = 1234
host = '127.0.0.1'

sock = socket(AF_INET, SOCK_STREAM)

server_address = (host, port)
sock.listen(1)

public_url = connect(port, "tcp", options={"remote_addr": f"{host}:{port}"})
print(public_url)

while True:
    sock.accept()
