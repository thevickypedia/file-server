from base64 import b64encode
from functools import partial
from http.server import SimpleHTTPRequestHandler, test
from os import environ, path
from socket import gethostbyname


class AuthHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: tuple, **kwargs: dict):
        self.allow_reuse_address = True
        username = kwargs.pop("username")
        password = kwargs.pop("password")
        self._auth = b64encode(f"{username}:{password}".encode()).decode()
        super().__init__(*args, **kwargs)

    def log_message(self, format_, *args):
        # todo: log args which tells the method type and status code
        pass

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Test"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        if not self.headers.get("Authorization"):
            self.do_AUTHHEAD()
            self.wfile.write(b"No auth header received")
        elif self.headers.get("Authorization") == "Basic " + self._auth:
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get("Authorization").encode())
            self.wfile.write(b"Not authenticated")


if __name__ == "__main__":
    handler_class = partial(
        AuthHTTPRequestHandler,
        username=environ.get('username'),
        password=environ.get('password'),
        directory=path.expanduser('~')
    )
    test(HandlerClass=handler_class, port=environ.get('port', 1234), bind=gethostbyname('localhost'))
