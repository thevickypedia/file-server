###### Versions Supported
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-385/)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-391/)

###### Language Stats
![Language count](https://img.shields.io/github/languages/count/thevickypedia/personal_cloud)
![Code coverage](https://img.shields.io/github/languages/top/thevickypedia/personal_cloud)

###### Repo Stats
[![GitHub](https://img.shields.io/github/license/thevickypedia/personal_cloud)](LICENSE)
[![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/personal_cloud)](https://api.github.com/repos/thevickypedia/personal_cloud)
[![GitHub code size](https://img.shields.io/github/languages/code-size/thevickypedia/personal_cloud)](https://api.github.com/repos/thevickypedia/personal_cloud)
[![LOC](https://img.shields.io/tokei/lines/github/thevickypedia/personal_cloud)](https://api.github.com/repos/thevickypedia/personal_cloud)

###### Code Stats
![Modules](https://img.shields.io/github/search/thevickypedia/personal_cloud/module)
![Python](https://img.shields.io/github/search/thevickypedia/personal_cloud/.py)

###### Deployments
[![Docs](https://img.shields.io/docsrs/docs/latest)](https://thevickypedia.github.io/personal_cloud/)

###### Activity
![Maintained](https://img.shields.io/maintenance/yes/2021)
[![GitHub Repo created](https://img.shields.io/date/1618966420)](https://api.github.com/repos/thevickypedia/personal_cloud)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/personal_cloud)](https://api.github.com/repos/thevickypedia/personal_cloud)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/personal_cloud)](https://api.github.com/repos/thevickypedia/personal_cloud)

# Personal Cloud with basic authentication
Set up a personal cloud to access files in local machine from anywhere on the internet.

## Setup:
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
###### To host on a custom port:<br>

<details>
  <summary>Tips on choosing port numbers.</summary>
<br>

  > :bulb: &nbsp; Categories of port numbers.

    Well-Known ports: 0 to 1023
    Registered ports: 1024 to 49151
    Dynamically available: 49152 to 65535

  > :bulb: &nbsp; Command to check current port usage.

  `netstat -anvp tcp | awk 'NR<3 || /LISTEN/'`

</details>

`port` - Choose a port number that's available.

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

  > Uses a random port number if [env var for port](https://github.com/thevickypedia/personal_cloud#environment-variables-optional) is not set.

#### Option 2:
- `python3 ngrok.py`

  > Uses the port number `4443` by default if [env var for port](https://github.com/thevickypedia/personal_cloud#environment-variables-optional) is not set.

### Run-book:
https://thevickypedia.github.io/personal_cloud/

> Generated using [`sphinx-autogen`](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

### Coding Standards:
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

### Pre-Commit
`pre-commit` will run `flake8` and `isort` to ensure proper coding standards along with [docs_generator](gen_docs.sh) 
to update the [runbook](#Run-book)
> `pre-commit run --all-files`

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
