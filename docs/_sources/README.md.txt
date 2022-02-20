###### Versions Supported
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)

###### Language Stats
![Language count](https://img.shields.io/github/languages/count/thevickypedia/personal-cloud)
![Code coverage](https://img.shields.io/github/languages/top/thevickypedia/personal-cloud)

###### Repo Stats
[![GitHub](https://img.shields.io/github/license/thevickypedia/personal-cloud)](https://github.com/thevickypedia/personal-cloud/blob/main/LICENSE)
[![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/personal-cloud)](https://api.github.com/repos/thevickypedia/personal-cloud)
[![GitHub code size](https://img.shields.io/github/languages/code-size/thevickypedia/personal-cloud)](https://api.github.com/repos/thevickypedia/personal-cloud)
[![LOC](https://img.shields.io/tokei/lines/github/thevickypedia/personal-cloud)](https://api.github.com/repos/thevickypedia/personal-cloud)

###### Code Stats
![Modules](https://img.shields.io/github/search/thevickypedia/personal-cloud/module)
![Python](https://img.shields.io/github/search/thevickypedia/personal-cloud/.py)

###### Activity
[![GitHub Repo created](https://img.shields.io/date/1618966420)](https://api.github.com/repos/thevickypedia/personal-cloud)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/personal-cloud)](https://api.github.com/repos/thevickypedia/personal-cloud)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/personal-cloud)](https://api.github.com/repos/thevickypedia/personal-cloud)

# File Server
Set up a file server to access files in local machine from anywhere on the internet.

## Setup
### Environment Variables Required:
`username` Username which will be required to access the server.
<br>
`password` Password to confirm identity.
<br>
`port` Port number using which the endpoint is to be accessed.
> Note: Uses the port number `4443` by default.

Another important variable:<br>
`host_path` - Path which is to be hosted.
> Note: Hosts the entire home page by default.

### Environment Variables Optional:
###### To get notified when a client connects to your server.<br>
`gmail_user` Username for a gmail account. 
<br>
`gmail_pass` Password for the gmail account.
<br>
`recipient` Recipient email address to whom the notification has to be sent.

<details>
  <summary>LOGOUT button and its functionality requires some changes to SimpleHTTPRequestHandler</summary>

###### [http > server.py > SimpleHTTPRequestHandler > list_directory()](https://docs.python.org/3/library/http.server.html#http.server.SimpleHTTPRequestHandler.do_GET)
```text
1. Create a button within the html body.
2. Create a script that does a POST call to the source endpoint.
3. Add a message in the POST call to read 'LOGOUT'
```
> :bulb: &nbsp; You can add more custom buttons by including JS, CSS in the HTML part in `list_directory()`
</details>

### Steps to host on the internet:
#### Setup ngrok:
- Download, Install and Setup [ngrok](https://ngrok.com/)

#### Initialize ngrok:
#### Option 1:
- `ngrok http $port`

  > Uses a random port number if env var for port.

#### Option 2:
- `python3 ngrok.py`

  > Uses the port number `4443` by default if env var for port.

### Run-book:
https://thevickypedia.github.io/personal-cloud/

> Generated using [`sphinx-autogen`](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

### Coding Standards:
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

### Pre-Commit
`pre-commit` will run `flake8` and `isort` to ensure proper coding standards along with [docs_generator](https://github.com/thevickypedia/personal-cloud/blob/main/gen_docs.sh) 
to update the [runbook](#Run-book)

> `pip install --no-cache --upgrade sphinx pre-commit recommonmark`

> `pre-commit run --all-files`

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](https://github.com/thevickypedia/personal-cloud/blob/main/LICENSE)
