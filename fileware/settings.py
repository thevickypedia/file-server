"""Place for all necessary arguments accessed across multiple modules."""

import time

_start_time = time.time()  # set to the current time to reset the auth headers when timeout is reached
_first_run = True  # set first_run to True to prompt first time auth regardless of stored cookies
_authenticated = False  # set to False for the appropriate message to be written in the HTML file
_renamed = []  # set to empty list to append dictionaries with re-namings done for index.html
