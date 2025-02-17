import os
import requests
import time

# Function to get the workflow run status
def get_workflow_run_status(owner, repo, run_id, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    return response.json()

# Function to trigger the Repo B workflow and wait for status
def trigger_and_wait_for_status():
    # Get the environment variables passed from GitHub Actions
    token = os.getenv("INPUT_TOKEN")
    repo_owner = os.getenv("INPUT_REPO_OWNER")
    repo_name = os.getenv("INPUT_REPO_NAME")
    event_type = os.getenv("INPUT_EVENT_TYPE", "trigger-workflow")
    
    # Trigger the workflow (you should have the run ID from the initial trigger)
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
    data = {
        "event_type": event_type
    }
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, json=data, headers=headers)

    # Check if the trigger was successful and get the run ID
    if response.status_code == 204:
        print(f"Successfully triggered workflow in {repo_owner}/{repo_name}")
        # You need to get the run ID, which could come from another part of the response
        # For simplicity, assume run_id is returned or stored earlier
        run_id = response.headers.get('X-GitHub-Request-Id')  # You may need a different way to retrieve the run_id
    else:
        print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        return

    # Start polling for status
    status = None
    timeout = 30 * 60  # Timeout after 30 minutes (in seconds)
    poll_interval = 30  # Poll every 30 seconds

    start_time = time.time()

    while status not in ['completed', 'failed', 'canceled']:
        # Check elapsed time to ensure we're not exceeding the timeout
        if time.time() - start_time > timeout:
            print("Timeout reached. Stopping status check.")
            break

        # Get the current status of the workflow run
        result = get_workflow_run_status(repo_owner, repo_name, run_id, token)
        status = result.get('status')

        # Print the current status
        print(f"Current status: {status}")

        # Wait for the next polling interval
        time.sleep(poll_interval)

    # Once the status is final, handle the conclusion
    if status == 'completed':
        conclusion = result.get('conclusion')
        print(f"Workflow finished with status: {status}")
        if conclusion == 'success':
            print(f"{repo_name} completed successfully.")
        elif conclusion == 'failure':
            print("Repo B failed.")
        else:
            print(f"{repo_name} was canceled.")
    else:
        print(f"Workflow was {status} without reaching 'completed'.")

# Run the function to trigger the workflow and wait for its status
trigger_and_wait_for_status()
