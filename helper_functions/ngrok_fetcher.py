"""
Notes:
    This is an ultimate guide to check if ngrok is already running in the background.
    Ngrok might be running on auto generated port? No problem, we can still track it.
"""

from os import environ
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


def get_ngrok():
    if validate := get_port():
        port = validate.split('.')[-1]
    else:
        if not (port := environ.get('PORT')):
            return

    try:
        response = get(f'http://{ip}:{port}/api/tunnels')
    except InvalidURL:
        return
    except ConnectionError:
        return

    tunnel = load(response.content.decode(), Loader=FullLoader)['tunnels']
    return tunnel[0].get('public_url')
