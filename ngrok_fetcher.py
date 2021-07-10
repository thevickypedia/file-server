"""
Notes:
    This is an ultimate guide to check if ngrok is already running in the background.
    Ngrok might be running on auto generated port? No problem, we can still track it.
"""

from os import environ
from logging import log, ERROR, INFO, WARNING
from socket import gethostbyname
from subprocess import check_output

from requests import get
from requests.exceptions import InvalidURL, ConnectionError
from yaml import load, FullLoader

ip = gethostbyname('localhost')


def get_port():
    """Alternate is to run `echo {root_password} | sudo -S lsof -PiTCP -sTCP:LISTEN | grep ngrok`"""
    pid_check = check_output("ps -ef | grep ngrok", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    extract = [id_.split()[1] for id_ in pid_list if id_ and '/bin/sh' not in id_ and 'grep ngrok' not in id_]
    if extract:
        active_sessions = check_output("netstat -anvp tcp | awk 'NR<3 || /LISTEN/' 2>&1;", shell=True).decode('utf-8')
        return ''.join([row.split()[3] for index, row in enumerate(active_sessions.split('\n')) for each_id in extract
                        if row and index > 1 and each_id in row.split() and row.split()[3].startswith(ip)])


if validate := get_port():
    port = validate.split('.')[-1]
    log(level=INFO, msg=f'Ngrok is running on PORT: {port}')
else:
    if not (port := environ.get('PORT')):
        log(level=WARNING,
            msg=f'Ngrok might not be running, and there is no PORT number specified in env var to run a manual check.')
        exit()
    else:
        log(level=WARNING,
            msg=f'Ngrok might not be running, but since an env var is set to {port} lets check against it.')

response = None
try:
    response = get(f'http://{ip}:{port}/api/tunnels')
except InvalidURL:
    log(level=ERROR, msg=f'Invalid URL. The port number: {port} mentioned in env var is invalid.')
    exit('Invalid URL')
except ConnectionError:
    log(level=ERROR, msg=f'Connection Error. Ngrok is not running with the specified port {port}')
    exit('ConnectionError')

tunnel = load(response.content.decode(), Loader=FullLoader)['tunnels']
print(tunnel[0].get('public_url'))
