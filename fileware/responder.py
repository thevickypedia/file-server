from http.server import HTTPServer
from socket import socket


class Response:
    """Class to format the response, so that it can be accessed as a property.

    >>> Response

    """

    def __init__(self, dictionary: dict):
        """Extracts the properties ``ok``, ``status`` and ``body`` from a dictionary.

        Args:
            dictionary: Takes a dictionary of key-value pairs as an argument.
        """
        self.raw: dict = dictionary
        self._server: HTTPServer = dictionary.get('server')
        self._socket: socket = dictionary.get('socket')
        self._url: str = dictionary.get('url')

    @property
    def server(self) -> HTTPServer:
        """Returns the extracted class variable.

        Returns:
            HTTPServer:
            Server class.
        """
        return self._server

    @property
    def socket(self) -> socket:
        """Returns the extracted class variable.

        Returns:
            socket:
            Socket connection.
        """
        return self._socket

    @property
    def url(self) -> str:
        """Returns the extracted class variable.

        Returns:
            str:
            URL.
        """
        return self._url

    def json(self) -> dict:
        """Returns a dictionary of the argument that was received during class initialization.

        Returns:
            dict:
            Returns the dictionary received as arg.
        """
        return self.raw
