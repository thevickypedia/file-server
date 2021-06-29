from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from logging import basicConfig, getLogger, INFO
from os import path, chdir, getcwd, environ, listdir, makedirs, remove
from pathlib import PurePath
from socket import gethostbyname
from socketserver import TCPServer
from subprocess import check_output
from threading import Thread
from time import sleep
from urllib.parse import urlparse, parse_qs


class NetworkManager(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        check_auth(hyperlink=self.path)
        if '?username=' not in self.path and '&password=' not in self.path:
            logger.info(f'Currently Accessing: {host_path + self.path}')  # self.path = current directory
        try:
            SimpleHTTPRequestHandler.do_GET(self)
        except (BrokenPipeError, OSError) as error:
            logger.error(error)

    def log_message(self, format_, *args) -> None:
        pass


def reset_auth():
    global login_attempts, thread
    thread = True
    logger.info('Started sleep timer for 5 Minutes.')
    sleep(300)
    logger.info('Time Up. Resetting login_attempts to 0.')
    login_attempts = 0
    thread = False
    return


# noinspection PyTypeChecker
def check_auth(hyperlink):
    global login_attempts
    if login_attempts >= 3 and '|bypass|' not in hyperlink:
        logger.warning(f'{login_attempts} failed login attempts has been detected.'
                       f'Login page has been blocked for 5 minutes.')
        chdir(script_path + '/block')
        if not thread:
            Thread(target=reset_auth).start()
        return
    if query_components := parse_qs(urlparse(hyperlink).query):
        username = query_components.get('username')[0]
        password = query_components.get('password')[0]
        if username == environ.get('USERNAME') and password == environ.get('PASSWORD'):
            if login_attempts:
                logger.info(f'User {username} successfully logged in after {login_attempts} attempts. '
                            f'Resetting login attempts to 0.')
                login_attempts = 0
            logger.info(f'Received username: {username} and password: {password}')
            logger.info(f'Granting Access to {host_path + hyperlink}')
            chdir(host_path)
        elif username and password:
            check_log_file = open(script_path + '/' + LOG_FILENAME, 'r').readlines()
            redirect = True
            for recheck in check_log_file:
                if f'username: {username} and password: {password}' in recheck:
                    redirect = False
            if redirect:
                logger.info(f'Failed login attempt: {login_attempts}. Attempts Remaining: {3 - login_attempts}')
                logger.info(f'Received username: {username} and password: {password}')
                logger.info(f'No access was granted. Redirected to {script_path}')
                login_attempts += 1
                chdir(script_path)
        else:
            logger.info('User tried to access the page without any credentials.')
            logger.info(f'No access was granted. Redirected to {script_path}')
            chdir(script_path)
    elif hyperlink == '/':
        chdir(script_path)


def initiate_host():
    logger.info('Initiating Server Host')
    print(f'Initiating Server Host at http://{host_ip}:{port} to serve {host_path}')
    try:
        TCPServer((host_ip, port), NetworkManager).serve_forever()
    except OSError as os_error:
        if str(os_error) == '[Errno 48] Address already in use':
            busy = check_output(f'netstat -vanp tcp | grep {port}', shell=True).decode('utf-8').split('\n')[0]
            pid = int(busy.split()[-4])
            action = str(busy.split()[5])
            if action == 'TIME_WAIT':
                print(f"Port {port} is currently on TIME-WAIT\nPID: {pid}\n"
                      f"Please wait while the remote TCP receives the acknowledgment of its connection termination "
                      f"request or use 'SO_REUSEADDR' to reuse the port.\n"
                      f"Implementation: https://stackoverflow.com/a/18858817")
            elif action == 'LISTEN':
                print(f"An active listener is in progress.\n"
                      f"PID: {pid}\n"
                      f"Usage: http://{host_ip}:{port}\n"
                      f"You can kill the process with 'kill -9 {pid}' if you wish to start a new session.")
            remove(LOG_FILENAME)
        else:
            print(f'Failed to initiate server with the error: {os_error}')
    except KeyboardInterrupt:
        if vol_host:
            from volume import Volume
            Volume(label=vol_name).stop_usage()
        logger.info('Stopping server host')
        print('Stopping server host')


if __name__ == '__main__':
    from volume import Volume

    if (user_ := environ.get('USERNAME')) and (pass_ := environ.get('PASSWORD')) and (port := int(environ.get('PORT'))):
        makedirs('logs') if 'logs' not in listdir(getcwd()) else None  # create logs directory if not found
        LOG_FILENAME = datetime.now().strftime('logs/private_cloud_%H:%M:%S_%d-%m-%Y.log')  # set log file name
        basicConfig(
            filename=LOG_FILENAME, level=INFO,
            format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
            datefmt='%b-%d-%Y %H:%M:%S'
        )
        logger = getLogger(PurePath(__file__).stem)  # gets current file name

        login_attempts, thread, vol_host = 0, False, False

        script_path = getcwd()  # current path of the script
        host_ip = gethostbyname('localhost')

        if (vol_name := environ.get('volume_name')) and (vol_name != 'None'):
            host_path = f"/Volumes/{vol_name}/"
            vol_host = True
        else:
            host_path = path.expanduser('~')  # path that will be hosted

        initiate_host()
    else:
        print('Please add the environment variables for USERNAME, PASSWORD and desired PORT')
