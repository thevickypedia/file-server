import os
import warnings
from typing import Union, AnyStr
from uuid import UUID

from . import env
from . import server


def serve(port: Union[int, str] = None, username: AnyStr = None, password: AnyStr = None, host_dir: AnyStr = None,
          ngrok_auth: Union[UUID, str] = None, gmail_user: str = None, gmail_pass: str = None,
          recipient: str = None) -> None:
    """Initiates the ``FileWare``.

    Args:
        port: Port number in which the file server is running.
        username: Username to access fileserver.
        password: Password to access fileserver.
        host_dir: Takes the path to serve as an argument. Can also be loaded via env vars.
        ngrok_auth: Ngrok auth token for tunneling.
        gmail_user: Username for email notification.
        gmail_pass: Password for email notification.
        recipient: Email address to receive notification.

    See Also:
        - All these arguments can be loaded via env vars by placing the key-value pairs in a ``.env`` file.
        - The ``.env`` file should be stored in the current working directory.
    """
    if port:
        env.port = port
    if gmail_user:
        env.gmail_user = gmail_user
    if gmail_pass:
        env.gmail_pass = gmail_pass
    if recipient:
        env.recipient = recipient
    if username:
        env.username = username
    if password:
        env.password = password
    if ngrok_auth:
        env.ngrok_auth = ngrok_auth
    if host_dir:
        if os.path.isdir(host_dir):
            env.host_dir = host_dir
        else:
            warnings.warn(f"The specified path: {host_dir} doesn't exist. Defaulting to {env.host_dir}")

    server.initiate_connection()
