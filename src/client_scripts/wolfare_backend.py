# wolfare-backend.py
# 
# This program provides useful functions to communicate between ui and
# the API server.
#                       Created by Nathadon Samairat 23 August 2024

import requests
import json

protocal = "http://"
server_ip = "127.0.0.1"
server_port = "2546"
server_url = protocal + server_ip + ":" + server_port

history_cache = {'History 1' : "", 'History 2' : "", 'History 3' : ""}
fetching = False
prompting = False
pushing = False

def saveCache(id, cache):
    print("Chat cache save at: ", id)
    history_cache[id] = cache

def sendRequest(method, message=None):
    try:
        if method == "News":
            response = requests.get(server_url + "/api/news")
            if response.status_code == 200:
                data = response.json()
                date = data.get("date")
                output = data.get("output")
                return date, output
            else:
                return "Error", f"Error while getting the output: {response.status_code}"
        elif method == "Prompt":
            response = requests.post(server_url + "/api/prompt", json={"content": message})
            if response.status_code == 200:
                data = response.json()
                output = str(data.get("output"))
                return output
            else:
                return "Error while getting the output" + str(response.status_code)
        elif method == "Push":
            # response = requests.post(server_url + "/api/add_data", json={"content": message})
            # if response.status_code == 200:
            #     return response
            # else:
            #     return "Error while getting the output" + str(response.status_code)
            return "This is our future plan"
        elif method == "PushJSON":
            response = requests.post(server_url + "/api/add_json_data", json=message)
            if response.status_code == 200:
                return response
            else:
                return "Error while getting the output" + str(response.status_code)
    except:
        return "Error while sending the request", None

def newsFormater(data):
    # TODO please format the news data
    pass

def dataInputFormater(data):
    # TODO please format the data
    pass

# returns - sanitized news, - date modified
def fetchNews():
    global fetching
    if fetching == False:
        fetching = True
        date, news = sendRequest("News")
        fetching = False
        return date, news
    else:
        return "Fail to retrieve latest date", "Waiting for the previous news to be fetched. please try again"

def sendPrompt(prompt):
    global prompting
    if prompting == False:
        prompting = True
        output = sendRequest("Prompt", prompt)
        prompting = False
        return output
    else:
        return "Waiting for the previous prompt to be fetched. please try again"

def pushToCloud(data):
    global pushing
    if pushing == False:
        pushing = True
        print(data)
        # output = sendRequest("PUSH", data)
        output = "TODO send the push request"
        pushing = False
        return output
    else:
        return "Waiting for the previous data to train our model and verifying. please try again"
    
def uploadFile(path_file):
    print(path_file)
    if not path_file.lower().endswith('.json'):
        return 2, "The file is not a JSON file."
    try:
        with open(path_file, 'r', encoding='utf-8') as file:
            data = file.read()
        json_data = json.loads(data)
        for i in range(100):
            sendRequest("PushJSON", json_data[i])
        return 0, None
    except json.JSONDecodeError as e:
        return 3, str(e)
    except Exception as e:
        return 4, str(e)