import json
import os
import requests
import sys
import time
from datetime import datetime

def trigger_workflow(token, repo, event_type, payload):
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "event_type": event_type,
        "client_payload": payload
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print("Workflow triggered successfully.")
    else:
        print("Failed to trigger workflow:", response.status_code, response.text)
        sys.exit(1)

def get_recent_workflow_run(token, repo, event, since_timestamp):
    url = f"https://api.github.com/repos/{repo}/actions/runs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error fetching workflow runs:", response.status_code, response.text)
        return None
    runs = response.json().get("workflow_runs", [])
    for run in runs:
        run_time_str = run.get("created_at")
        run_datetime = datetime.strptime(run_time_str, "%Y-%m-%dT%H:%M:%SZ")
        if run_datetime.timestamp() >= since_timestamp:
            return run
    return None

def poll_workflow_run_status(token, repo, run_id, poll_interval=10, timeout=600):
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    start_time = time.time()
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error fetching run status:", response.status_code, response.text)
            return None
        run_data = response.json()
        status = run_data.get("status")
        conclusion = run_data.get("conclusion")
        print(f"Workflow run status: {status}")
        if status == "completed":
            print(f"Workflow run completed with conclusion: {conclusion}")
            return conclusion
        if time.time() - start_time > timeout:
            print("Timed out waiting for the workflow run to complete.")
            return None
        time.sleep(poll_interval)

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    event_type = os.getenv("GITHUB_EVENT_TYPE")
    payload_str = os.getenv("GITHUB_PAYLOAD", "{}")

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        print("Invalid JSON payload")
        sys.exit(1)

    start_timestamp = time.time()
    trigger_workflow(token, repo, event_type, payload)
    
    print("Waiting for the workflow run to be created...")
    run = None
    max_wait = 60
    waited = 0
    while run is None and waited < max_wait:
        run = get_recent_workflow_run(token, repo, "repository_dispatch", start_timestamp)
        if run is None:
            time.sleep(5)
            waited += 5
    if run is None:
        print("Workflow run did not appear within the expected time.")
        sys.exit(1)

    run_id = run.get("id")
    print(f"Found workflow run with ID: {run_id}. Now waiting for its completion...")
    conclusion = poll_workflow_run_status(token, repo, run_id)

    print(f"Workflow run finished with conclusion: {conclusion}")
    sys.exit(0 if conclusion == "success" else 1)

if __name__ == "__main__":
    main()
