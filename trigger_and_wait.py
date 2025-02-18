import sys
import os
import requests
import time

github_repository = os.getenv("GITHUB_REPOSITORY")  
if github_repository:
    owner, repo = github_repository.split("/")
else:
    print("GITHUB_REPOSITORY environment variable is not set.")

token = os.getenv("INPUT_TOKEN")
if not token:
    print("Error: TOKEN is not set.")
    sys.exit(1)
event_type = os.getenv("INPUT_EVENT_TYPE", "trigger-workflow")

def get_api_base_url():
    return os.getenv('GITHUB_API_URL', 'https://api.github.com')
base_url = get_api_base_url()


def trigger_workflow(owner, repo, token, event_type):

    url = f"{base_url}/repos/{owner}/{repo}/dispatches"
    data = {
        "event_type": event_type
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"  
    }
    response = requests.post(url, json=data, headers=headers)


    if response.status_code != 204:
        print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        sys.exit(1)        
    print(f"Successfully triggered workflow in {owner}/{repo}")


trigger_workflow(owner, repo, token, event_type)
