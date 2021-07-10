# Personal Cloud with basic authentication
Set up a personal cloud to access files in local machine from anywhere on the internet.

## Run Book:
### Environment Variables Required:
`USERNAME` Username which will be required to access the server.
<br>
`PASSWORD` Password to confirm identity.
<br>
`PORT` Port number using which the endpoint is to be accessed.
> Note: Uses the port number `4443` by default.

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

### Environment Variables Optional:
To get notified when a client connects to your server.<br>
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
- Open a new terminal tab/window and run `ngrok http $PORT`
- Once the `Session Status` shows `Online` and turns green, copy the `Forwarding` endpoint.
- Use the `http` or `https` endpoint and start browsing your local content from anywhere on the internet.
#### Option 2:
- Install the requirements to initiate ngrok using python `pip3 install -r requirements.txt`
- Check if the port env var is set properly by running `echo $PORT`
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

[comment]: <> (### Future iterations:)
[comment]: <> (1. Onboard Volumes and session trackers.)
[comment]: <> (2. Serve [auth_server.html]&#40;auth_server.html&#41; as run-time info rather a file, to support welcome screen on ext volumes.)
[comment]: <> (3. Block repeated-failed sessions and probably extend automatic session expiry.)
[comment]: <> (4. Plan on adding auto-reboot.)

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
