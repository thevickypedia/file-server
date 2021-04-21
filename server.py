from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from logging import basicConfig, getLogger, INFO
from os import getcwd, environ, listdir, system as executor
from socketserver import TCPServer
from threading import Thread

# create logs directory if not found
executor(f'mkdir logs') if 'logs' not in listdir(getcwd()) else None

# initiate logger
LOG_FILENAME = datetime.now().strftime('logs/private_cloud_%H:%M:%S_%d-%m-%Y.log')
basicConfig(filename=LOG_FILENAME, level=INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = getLogger(__name__)


class NetworkManager(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        logger.info(f'Currently Displaying: {self.path}')  # self.path will be the current directory displayed as /
        SimpleHTTPRequestHandler.do_GET(self)


def initiate_host():
    host = '127.0.0.1'
    logger.info(f'Access it using http://{host}:{port}')
    try:
        handler = TCPServer((host, port), NetworkManager)
        handler.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError as os_error:
        if str(os_error) == '[Errno 48] Address already in use':
            # todo: check for 256 output and skip it as that's from the os module
            print(f"Port {port} is busy. Currently used by the PID {executor(f'lsof -i :{port}')}")


if __name__ == '__main__':
    if (port := int(environ.get('PORT'))) and (user_ := environ.get('USER')) and (pass_ := environ.get('PASS')):
        Thread(target=initiate_host).start()
    else:
        print('Please add the environment variables for USER, PASS and desired PORT')
