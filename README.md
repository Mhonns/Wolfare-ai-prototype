# Cyber Security News & Chatbot Project

## Disclaimer
This project is currently in the development phase. If you encounter any bugs during testing, please feel free to reach out. The current model has been fine-tuned using cyber security data from various sources, including the Hacker News dataset and cyber security summaries from developers (e.g., SIEM tools manuals).

## Objective
The goal of this project is to create a tool for Security Operation Centers (SOCs) that enables them to:
- Receive the most recent cyber security news.
- Interact with a personalized chatbot specialized in cyber security.
- Train the chatbot with specific cyber security knowledge.

## How to Run (Prototype)
0. Prerequisites
Please ensure that python3, python3-pip were installed which enable to be executed via CLI.
1. Clone the project to your machine and navigate to the `src/client_scripts` directory:
```console
$ cd src/client_scripts
```
2. Install the required dependencies:
```console
$ pip3 install -r requirements.txt
```
3. Run the service (controller):
```console
$ python3 wolfare_controller.py
```
4. [Optional] For windows user please run
```console
$ python3 wolfare_controller_win.py
```

## How to deploy the server (Prototype)
0. Prerequisites
Please ensure that python3, python3-pip were installed which enable to be executed via CLI.
1. Clone the project to your machine and navigate to the `src/server_scripts` directory:
```console
$ cd src/client_scripts
```
2. Install the required dependencies:
```console
$ pip3 install -r requirements.txt
```
3. To deploy the server please run
```console
$ python3 api_server.py
```
## Manual 
0. After running the server, To open the GUI press ctrl + h on the keyboard.
1. To close the gui please ctrl + once again.
2. To close the service user can