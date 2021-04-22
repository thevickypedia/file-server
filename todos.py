"""
Short Term
# todo: sync sleep time in python script with the timer in html page
# todo: have a drop down button as 'Categories' for Movies, Music and Images
# todo: For images add MFA using AWS SNS to trigger a random generated integer code and validate before granting access
# todo: hash the hyperlink in html using js and compare it against hashed value of username and password
# todo: create a cert and bind to the local host server and make ngrok use https forwarding for tcp tunnels

Long Term
# TODO: host a static page for authentication on AWS S3 and connect it with AWS API Gateway
        to send the credentials to a lambda function. And then,
        1. Check if credentials match using lambda and then forward to ngrok - TCP connection is at risk in this case
        (or)
        2. Hash the credentials in lambda and send it to server.py using ngrok, and match the hashed value in python
        (or)
        3. Do (1) and add MFA when connection is sent from lambda to server.py
# todo: get rid of static html and using jinja template or similar for easy iterations in future
# todo: host the webpage using flask or django
"""