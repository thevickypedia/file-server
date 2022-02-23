**Versions Supported**

![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)

**Language Stats**

![Language count](https://img.shields.io/github/languages/count/thevickypedia/fileware)
![Code coverage](https://img.shields.io/github/languages/top/thevickypedia/fileware)

**Repo Stats**

[![GitHub](https://img.shields.io/github/license/thevickypedia/fileware)](https://github.com/thevickypedia/fileware/blob/main/LICENSE)
[![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/fileware)](https://api.github.com/repos/thevickypedia/fileware)
[![GitHub code size](https://img.shields.io/github/languages/code-size/thevickypedia/fileware)](https://api.github.com/repos/thevickypedia/fileware)
[![LOC](https://img.shields.io/tokei/lines/github/thevickypedia/fileware)](https://api.github.com/repos/thevickypedia/fileware)

**Code Stats**

![Modules](https://img.shields.io/github/search/thevickypedia/fileware/module)
![Python](https://img.shields.io/github/search/thevickypedia/fileware/.py)

**Activity**

[![GitHub Repo created](https://img.shields.io/date/1618966420)](https://api.github.com/repos/thevickypedia/fileware)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/fileware)](https://api.github.com/repos/thevickypedia/fileware)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/fileware)](https://api.github.com/repos/thevickypedia/fileware)

**Build Status**

[![pypi-publish](https://github.com/thevickypedia/gmail-connector/actions/workflows/python-publish.yml/badge.svg)](https://github.com/thevickypedia/gmail-connector/actions/workflows/python-publish.yml)
[![pages-build-deployment](https://github.com/thevickypedia/gmail-connector/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/thevickypedia/gmail-connector/actions/workflows/pages/pages-build-deployment)

# FileWare
Set up a file server to access files in local machine from anywhere on the internet.

### Setup
**Environment Variables:**

- `username`: Username to confirm identity. Defaults to user profile name.
- `password`: Password for authentication. Defaults to `FileServer`
- `port`: Port number to serve. Defaults to `4443`.
- `host_path`: Path which is to be hosted. Defaults to `home` page.

**To enable notifications during connections:**

- `gmail_user`: Username for a gmail account.
- `gmail_pass`: Password for the gmail account.
- `recipient`: Recipient email address.

**To host on a public facing URL:**
- `ngrok_auth`: Ngrok token.

### Usage

```shell
python3 -m pip install fileware
```

**With Threading**
```python
import time
from threading import Thread

import fileware


# [OPTIONAL] - Override env vars for distributed usage or multiple ngrok accounts.
fileware.override_env_vars(
    gmail_user="Username@gmail.com",
    gmail_pass="xxxxxxxxxx",
    recipient="Recipient@gmail.com",
    password="FileServer",
    ngrok_auth="***********************"
)

# Initiates the connection and creates a new process if ngrok auth token is valid.
response = fileware.initiate_connection()
print(response.url)

# Runs the server in a thread alongside starting the ngrok process created previously.
thread = Thread(target=fileware.serve,
                kwargs={'http_server': response.server, 'process': response.process})
thread.start()

# Sleep or any other task in parallel.
time.sleep(6e+1)

# Shutdown the server and join the thread which spun the server up.
fileware.shutdown(http_server=response.server, process=response.process)
thread.join(2e+1)
```

**Without Threading - File Server will terminate only when the main process is killed.**
```python
import fileware

response = fileware.initiate_connection()
print(response.url)

fileware.serve(http_server=response.server,process=response.process)
```

> Env vars can be loaded by placing a .env file in current working directory.
>
> The `serve` function can also take arguments which can be used to override env vars.

### Pypi Package
[![pypi-module](https://img.shields.io/badge/Software%20Repository-pypi-1f425f.svg)](https://packaging.python.org/tutorials/packaging-projects/)

[https://pypi.org/project/fileware/](https://pypi.org/project/fileware/)

### Runbook
[![made-with-sphinx-doc](https://img.shields.io/badge/Code%20Docs-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

[https://thevickypedia.github.io/fileware/](https://thevickypedia.github.io/fileware/)

**Run-book:**

https://thevickypedia.github.io/fileware/

> Generated using [`sphinx-autogen`](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

**Coding Standards:**

Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

**Pre-Commit**

`pre-commit` will run `flake8` and `isort` to ensure proper coding standards along with [docs_generator](https://github.com/thevickypedia/fileware/blob/main/gen_docs.sh) 
to update the runbook.

> `pip install --no-cache --upgrade sphinx pre-commit recommonmark`

> `pre-commit run --all-files`

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](https://github.com/thevickypedia/fileware/blob/main/LICENSE)
