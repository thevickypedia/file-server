"""Place for all necessary arguments accessed across multiple modules."""
import getpass
import os
import socket
from time import time

import dotenv

if os.path.isfile('.env'):
    dotenv.load_dotenv(dotenv_path='.env')

start_time = time()  # set to the current time to reset the auth headers when timeout is reached
first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
authenticated = False  # set to False for the appropriate message to be written in the HTML file
renamed = []  # set to empty list to append dictionaries with re-namings done for index.html

STOPPER = False

host = socket.gethostbyname('localhost')
port = int(os.environ.get('port', 4443))

gmail_user = os.environ.get('gmail_user')
gmail_pass = os.environ.get('gmail_pass')
recipient = os.environ.get('recipient')
username = os.environ.get('username', os.environ.get('USER', getpass.getuser()))
password = os.environ.get('password', 'FileServer')
home_dir = os.path.expanduser('~')
host_dir = os.environ.get('host_path', home_dir)
ngrok_auth = os.environ.get('ngrok_auth')
