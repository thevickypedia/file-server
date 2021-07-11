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

> Tip:bulb: &nbsp; Save the env vars (specifically, `PORT`) in `.bashrc`/`.zshrc` or `.bash_profile`/`.zsh_profile` so that, the vars are set during launch and can be accessed across multiple terminal sessions.

Another important variable:<br>
`host_path` - Path which is to be hosted.
> Note: Hosts the entire home page by default.

### Environment Variables Optional:
###### To host on a custom port:<br>
```text
Well-Known ports: 0 to 1023
Registered ports: 1024 to 49151
Dynamically available: 49152 to 65535
```
Command to check current port usage:<br>
`netstat -anvp tcp | awk 'NR<3 || /LISTEN/'`

`port` - Choose a port number that's available.

###### To get notified when a client connects to your server.<br>
`gmail_user` Username for a gmail account. 
<br>
`gmail_pass` Password for the gmail account.
<br>
`recipient` Recipient email address to whom the notification has to be sent.

### Steps to host on the internet:
#### Setup ngrok:
- Download, Install and Setup [ngrok](https://ngrok.com/)

#### Initialize ngrok:
#### Option 1:
- Initiate the server by running `python3 authserver.py`
- Open a new terminal tab/window and run `ngrok http $port`
- Once the `Session Status` shows `Online` and turns green, copy the `Forwarding` endpoint.
- Use the `http` or `https` endpoint and start browsing your local content from anywhere on the internet.
#### Option 2:
- Install the requirements to initiate ngrok using python `pip3 install -r requirements.txt`
- Trigger the ngrok script to trigger ngrok and listen for connections `python3 ngrok.py`
- Logger information will print the endpoint to access the origin.
  - Example: `http://t4adsf328a.ngrok.io` which can also be accessed via `https://t4adsf328a.ngrok.io`
  > Note: Uses the port number `4443` by default.

### Webpage Functionalities:
- [AuthServer](authserver.py) uses encrypted server side header authentication.
- Browser's default pop up will be shown prompting the user to enter the username and password.
- Enter the Username and Password that was set in [environment variables](https://github.com/thevickypedia/personal_cloud/blob/main/README.md#environment-variables-required)
- The username and password are set as encoded auth headers, which are matched against the encoded env vars.
- Upon successful authentication, a welcome page loads. Click on the [proceed](#) button to hop on to the PersonalCloud.
- For lack of logout option, a session expiry has been set every 15 minutes, forcing the user to do a re-auth.

> Note: Incorrect authentication is not an option since auth headers are a strict match. However, on the bright side, 
> client IP and session information is tracked, logged and notified. On the downside, there is no limit on login 
> attempts.

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
> Command: `pre-commit run --all-files`

#### Usage:
<h6>Manual: <code>cd doc_generator && make html</code><h6>
<h6>Auto: The autodoc generation will run as part of <code>pre-commit</code></h6>

[comment]: <> (### Future iterations:)
[comment]: <> (1. Block repeated-failed sessions and probably extend automatic session expiry.)

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
