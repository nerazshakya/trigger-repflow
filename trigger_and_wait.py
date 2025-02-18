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


def get_workflow_run_status(owner, repo, run_id, token):
    url = f"{base_url}/repos/{owner}/{repo}/actions/runs/{run_id}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        'Authorization': f'token {token}'
        }
    response = requests.get(url, headers=headers)
    return response.json()

def trigger_and_wait_for_status(owner, repo, token, event_type):

    url = f"{base_url}/repos/{owner}/{repo}/dispatches"
    data = {
        "event_type": event_type
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"  
    }
    response = requests.post(url, json=data, headers=headers)

    # Check if the trigger was successful and get the run ID
    if response.status_code != 204:
        print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        sys.exit(1)  # Exit with error code if the trigger fails        
    print(f"Successfully triggered workflow in {owner}/{repo}")
    run_id = response.headers.get('X-GitHub-Request-Id')  # You may need a different way to retrieve the run_id

    # Start polling for status
    status = None
    timeout = 30 * 60  # Timeout after 30 minutes (in seconds)
    poll_interval = 30  # Poll every 30 seconds

    start_time = time.time()

    while status not in ['completed', 'failed', 'canceled']:
        # Check elapsed time to ensure we're not exceeding the timeout
        if time.time() - start_time > timeout:
            print("Timeout reached. Stopping status check.")
            sys.exit(1)  # Exit with error code if the timeout is reached

        # Get the current status of the workflow run
        result = get_workflow_run_status(owner, repo, run_id, token)
        status = result.get('status')
        print(f"Current status: {status}")
        time.sleep(poll_interval)

    # Once the status is final, handle the conclusion
    if status == 'completed':
        conclusion = result.get('conclusion')
        print(f"Workflow finished with status: {status}")
        if conclusion == 'success':
            print(f"{repo} completed successfully.")
        elif conclusion == 'failure':
            print(f"{repo} failed.")
            sys.exit(1)
        else:
            print(f"{repo} was canceled.")
            sys.exit(1)
    else:
        print(f"Workflow was {status} without reaching 'completed'.")
        sys.exit(1)

# Run the function to trigger the workflow and wait for its status
trigger_and_wait_for_status(owner, repo, token, event_type)
