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
                output = data.get("output")
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

def newsFormater(json_string):
    json_string = json_string.strip("```json").strip("```")
    data = json.loads(json_string)
    html = ""
    # Title
    html += f"<title>{data['title']['original']}</title>\n"
    # Type
    html += f"<h1>Type</h1>\n"
    html += f"<p>{data['type']}</p>\n"
    
    # Overview
    html += f"<h2>Overview</h2>\n"
    html += f"<p>{data['overview']}</p>\n"

    # Threat Analysis
    html += f"<h2>Threat Analysis</h2>\n"
    html += f"<p>Threat Level: {data['threat_analysis']['threat_level']}</p>\n"
    html += f"<p>Affected Systems: {', '.join(data['threat_analysis']['affected_systems'])}</p>\n"
    html += f"<p>Potential Impact: {data['threat_analysis']['potential_impact']}</p>\n"

    # Key Points
    html += f"<h2>Key Points</h2>\n"
    for point in data['key_points']:
        html += f"<h3>{point['category']}</h3>\n"
        html += f"<p>{point['description']}</p>\n"
        html += f"<p>Relevance: {point['relevance']}</p>\n"

    # Technical Details
    html += f"<h2>Technical Details</h2>\n"
    html += f"<p>CVE IDs: {', '.join(data['technical_details']['cve_ids']) if data['technical_details']['cve_ids'] else 'None'}</p>\n"
    html += f"<p>IOCs: {', '.join(data['technical_details']['iocs']) if data['technical_details']['iocs'] else 'None'}</p>\n"
    # html += f"<p>Affected Versions: {', '.join(data['technical_details']['affected_versions'])}</p>\n"

    # Actionable Insights
    html += f"<h2>Actionable Insights</h2>\n"
    for insight in data['actionable_insights']:
        html += f"<h3>Priority: {insight['priority']}</h3>\n"
        html += f"<p>Action: {insight['action']}</p>\n"
        html += f"<p>Rationale: {insight['rationale']}</p>\n"

    # Related Topics
    html += f"<h2>Related Topics</h2>\n"
    html += f"<ul>\n"
    for topic in data['related_topics']:
        html += f"<li>{topic}</li>\n"
    html += f"</ul>\n"

    return html

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
        if news != None:
            news = newsFormater(news)
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