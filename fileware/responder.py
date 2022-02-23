from http.server import HTTPServer
from multiprocessing import Process


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
        self._url: str = dictionary.get('url')
        self._server: HTTPServer = dictionary.get('server')
        self._process: Process = dictionary.get('process')

    @property
    def url(self) -> str:
        """Returns the extracted class variable.

        Returns:
            str:
            Public URL from Ngrok or the local IP based endpoint.
        """
        return self._url

    @property
    def server(self) -> HTTPServer:
        """Returns the extracted class variable.

        Returns:
            HTTPServer:
            Web Server object.
        """
        return self._server

    @property
    def process(self) -> Process:
        """Returns the extracted class variable.

        Returns:
            Process:
            Process for Ngrok.
        """
        return self._process

    def json(self) -> dict:
        """Returns a dictionary of the argument that was received during class initialization.

        Returns:
            dict:
            Returns the dictionary received as arg.
        """
        return self.raw
