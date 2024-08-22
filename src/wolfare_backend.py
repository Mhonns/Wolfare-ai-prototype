# wolfare-backend.py
# 
# This program provides useful functions to communicate between ui and
# the API server.
#                       Created by Nathadon Samairat 23 August 2024

import requests

def sanitize():
    pass

# returns - sanitized news, - date modified
def formatReceivedNews():
    pass

def formatUserPrompt(prompt):
    pass

def formatUploadData():
    pass

def sendRequest(message):
    try:
        # Send a POST request to the server
        response = requests.post(server_url, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
