# from yaml import load, FullLoader
# from urllib.request import urlopen
# print(load(urlopen('http://checkip.amazonaws.com'), Loader=FullLoader))
# # print(load(urlopen('http://myip.dnsomatic.com'), Loader=FullLoader))
# print()
from logging import getLogger

from helper_functions.ngrok import starter

getLogger('ngrok').propagate = False
print(starter())
