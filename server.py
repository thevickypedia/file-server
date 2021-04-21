from http.server import SimpleHTTPRequestHandler
from os import environ
from socketserver import TCPServer
from threading import Thread


class NetworkManager(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        print(f'Currently Displaying: {self.path}')  # self.path will be the current directory displayed as /
        SimpleHTTPRequestHandler.do_GET(self)


def initiate_host():
    host = '127.0.0.1'
    print(f'Access it using http://{host}:{port}')
    try:
        TCPServer((host, port), NetworkManager).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    if (port := int(environ.get('PORT'))) and (user_ := environ.get('USER')) and (pass_ := environ.get('PASS')):
        Thread(target=initiate_host).start()
    else:
        print('Please add the environment variables for USER, PASS and desired PORT')
