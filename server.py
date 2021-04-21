from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from logging import basicConfig, getLogger, INFO
from os import path, chdir, getcwd, environ, listdir, system as executor
from socketserver import TCPServer
from subprocess import check_output, SubprocessError
from threading import Thread

# create logs directory if not found
executor(f'mkdir logs') if 'logs' not in listdir(getcwd()) else None

# initiate logger
LOG_FILENAME = datetime.now().strftime('logs/private_cloud_%H:%M:%S_%d-%m-%Y.log')
basicConfig(filename=LOG_FILENAME, level=INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = getLogger(__name__)

# Change this path to the directory on your computer which you want to make accessible by the server.
# Currently set to the user's home directory
host_path = path.expanduser('~')


class NetworkManager(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        logger.info(f'Currently Accessing: {host_path + self.path}')  # self.path = current directory
        SimpleHTTPRequestHandler.do_GET(self)


def initiate_host():
    host = '127.0.0.1'
    logger.info(f'Access it using http://{host}:{port}')
    try:
        chdir(host_path)
        TCPServer((host, port), NetworkManager).serve_forever()
    except OSError as os_error:
        if str(os_error) == '[Errno 48] Address already in use':
            try:
                busy = check_output(f'lsof -i :{port}', shell=True).decode('utf-8').split('\n')[0]
                print(f"Port {port} is busy. Currently used by the PID {busy}")
            except SubprocessError as subprocess_error:
                if str(subprocess_error) == f"Command 'lsof -i :{port}' returned non-zero exit status 1.":
                    print(f"Port {port} was temporarily busy. Please retry.")
                else:
                    print(f'Failed to initiate server with the error: {subprocess_error}')
        else:
            print(f'Failed to initiate server with the error: {os_error}')


if __name__ == '__main__':
    if (port := int(environ.get('PORT'))) and (user_ := environ.get('USER')) and (pass_ := environ.get('PASS')):
        Thread(target=initiate_host).start()
    else:
        print('Please add the environment variables for USER, PASS and desired PORT')
