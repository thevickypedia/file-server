# Personal Cloud with basic authentication
Set up a personal cloud to access files in local machine from anywhere on the internet.

## Run Book:
### Environment Variables Required:
`USERNAME` Username which will be required to access the server.
<br>
`PASSWORD` Password to confirm identity.
<br>
`PORT` Port number using which the endpoint is to be accessed.

Example:
```
export USERNAME=IronMan
export PASSWORD=Jarvis
export PORT=0502
```
> Tip:bulb: &nbsp; Save the env vars (specifically, `PORT`) in `.bashrc`/`.zshrc` or `.bash_profile`/`.zsh_profile` so that, the vars are set during launch and can be accessed across multiple terminal sessions.

Another important variable:<br>
`host_path` - Path which is to be hosted.
> Note: Hosts the entire home page by default.

### Steps to host on the internet:
- Download, Install and Setup [ngrok](https://ngrok.com/)
- Set the [environment variables](https://github.com/thevickypedia/personal_cloud/blob/main/README.md#environment-variables-required)
- Make sure `host_path` variable is set to the path that needs to be hosted.
- Check if the port env var is set properly by running `echo $PORT`
- Initiate the server by running `python3 server.py`
- Open a new terminal tab/window and run `ngrok tcp $PORT`
- Once the `Session Status` shows `Online` and turns green, copy the `Forwarding` endpoint.
- Replace the `tcp` with `http` and start browsing your local content from anywhere on the internet.
   - Example: `tcp://37.tcp.ngrok.io:12345` &#8594; `http://37.tcp.ngrok.io:12345`

### Webpage Functionalities:
- Enter the Username and Password that was set in [environment variables](https://github.com/thevickypedia/personal_cloud/blob/main/README.md#environment-variables-required)
   - The webpage uses a `javascript` to disable the `Authenticate` button until some text is entered in the `Username` and `Password` fields.
- Click the `Authenticate` button.
   - This will change the URL to a pre-signed URL with the entered `Username` and `Password`
- Click on the [Clockwise Gapped Circle Arrow](https://www.toptal.com/designers/htmlarrows/arrows/clockwise-gapped-circle-arrow/)
   - This will reload the pre-signed URL allowing the user to access the file server, if the username and password matches server's env vars.
- In case of incorrect `Username` and `Password` for 5 consecutive attempts, the server will lock itself for 5 minutes. User will be redirected to a waiting page with a timer displayed.
   - The timer will not reset itself unless a hard refresh is done.

> :warning: &nbsp; DISCLAIMER: Neither `USERNAME` nor `PASSWORD` is encrypted. In fact, the script uses the header on the html page to fetch username and password to authenticate. So use this script at your own risk.

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
