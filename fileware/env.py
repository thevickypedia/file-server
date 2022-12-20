"""Place for all necessary env vars accessed across multiple modules."""
import getpass
import os

import dotenv

from . import settings

if os.path.isfile('.env'):
    dotenv.load_dotenv(dotenv_path='.env')

port = int(os.environ.get('port', 4443))

username = os.environ.get('username', os.environ.get('USER', getpass.getuser()))
password = os.environ.get('password')
host_dir = os.environ.get('host_path', settings._home_dir)  # noqa: PyProtectedMember
ngrok_auth = os.environ.get('ngrok_auth')
