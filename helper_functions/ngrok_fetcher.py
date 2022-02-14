"""Identifies if an existing ngrok tunnel."""

from os import environ
from socket import gethostbyname
from subprocess import check_output

from requests import get
from requests.exceptions import ConnectionError, InvalidURL
from yaml import FullLoader, load

ip = gethostbyname('localhost')


def get_port() -> str:
    """Looks for ngrok processID. If found, scans the PID in `netstat` for an `activeListener` to skim the port number.

    Notes:
        Alternate is to run `echo {root_password} | sudo -S lsof -PiTCP -sTCP:LISTEN | grep ngrok`

    Returns:
        str:
        Local IP address and port number on which ngrok is tunnelling.
    """
    pid_check = check_output("ps -ef | grep ngrok", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    extract = [id_.split()[1] for id_ in pid_list if id_ and '/bin/sh' not in id_ and 'grep ngrok' not in id_]
    if extract:
        active_sessions = check_output("netstat -anvp tcp | awk 'NR<3 || /LISTEN/' 2>&1;", shell=True).decode('utf-8')
        return ''.join([row.split()[3] for index, row in enumerate(active_sessions.split('\n')) for each_id in extract
                        if row and index > 1 and each_id in row.split() and row.split()[3].startswith(ip)])


def get_ngrok() -> str or None:
    """Sends a `GET` request to api/tunnels to get the `ngrok` public url.

    See Also:
        Checks for output from get_port function. If nothing, then `ngrok` isn't running.
        However, as a sanity check, the script uses port number stored in env var to make a `GET` request.

    Returns:
        str or None:
        - On success, returns the `ngrok` public URL.
        - On failure, returns None to exit function.
    """
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


if __name__ == '__main__':
    print(get_ngrok())
