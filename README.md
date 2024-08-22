# Cyber Security News & Chatbot Project

## Disclaimer
This project is currently in the development phase. If you encounter any bugs during testing, please feel free to reach out. The current model has been fine-tuned using cyber security data from various sources, including the Hacker News dataset and cyber security summaries from developers (e.g., SIEM tools manuals).

## Objective
The goal of this project is to create a tool for Security Operation Centers (SOCs) that enables them to:
- Receive the most recent cyber security news.
- Interact with a personalized chatbot specialized in cyber security.
- Train the chatbot with specific cyber security knowledge.

## How to Run (Prototype)
1. Clone the project to your machine and navigate to the `src` directory:
```console
$ cd src/client_scripts
```
2. Install the required dependencies:
```console
$ pip3 install -r requirements.txt
```
3. Run the service (controller):
```console
$ python3 wolfare-controller.py
```